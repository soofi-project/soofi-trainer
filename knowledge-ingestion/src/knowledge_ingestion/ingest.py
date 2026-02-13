"""One-shot knowledge ingestion pipeline for Soofi Trainer.

Scans markdown files in the knowledge directory, computes change detection
via SHA-256 hashes, chunks documents, embeds them, and upserts into Weaviate.
"""

import hashlib
import logging
import os
import time
from pathlib import Path
from typing import Any

import weaviate
import yaml
from langchain.embeddings.base import init_embeddings
from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter
from weaviate.classes.config import DataType, Property
from weaviate.classes.query import Filter

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
KNOWLEDGE_DIR = Path("/app/knowledge")
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
WEAVIATE_CONNECT_RETRIES = 5
WEAVIATE_CONNECT_DELAY = 5  # seconds

COLLECTION_PROPERTIES = [
    Property(name="text", data_type=DataType.TEXT),
    Property(name="topic", data_type=DataType.TEXT),
    Property(name="category", data_type=DataType.TEXT),
    Property(name="source", data_type=DataType.TEXT),
    Property(name="source_hash", data_type=DataType.TEXT),
]

MD_HEADERS_TO_SPLIT = [
    ("#", "h1"),
    ("##", "h2"),
    ("###", "h3"),
]


# ---------------------------------------------------------------------------
# Weaviate connection with retry
# ---------------------------------------------------------------------------
def connect_weaviate() -> weaviate.WeaviateClient:
    """Connect to Weaviate with retry logic."""
    host = os.getenv("WEAVIATE_HOST", "weaviate")
    port = int(os.getenv("WEAVIATE_PORT", "8080"))

    last_exc: Exception | None = None
    for attempt in range(1, WEAVIATE_CONNECT_RETRIES + 1):
        try:
            client = weaviate.connect_to_local(host=host, port=port)
            logger.info("Connected to Weaviate at %s:%s", host, port)
            return client
        except Exception as exc:
            last_exc = exc
            if attempt < WEAVIATE_CONNECT_RETRIES:
                logger.warning(
                    "Weaviate connection attempt %d/%d failed: %s — retrying in %ds",
                    attempt,
                    WEAVIATE_CONNECT_RETRIES,
                    exc,
                    WEAVIATE_CONNECT_DELAY,
                )
                time.sleep(WEAVIATE_CONNECT_DELAY)

    raise RuntimeError(
        f"Could not connect to Weaviate after {WEAVIATE_CONNECT_RETRIES} attempts"
    ) from last_exc


# ---------------------------------------------------------------------------
# Collection management
# ---------------------------------------------------------------------------
def ensure_collection(client: weaviate.WeaviateClient, name: str) -> Any:
    """Create the collection if it does not exist, then return a handle."""
    if not client.collections.exists(name):
        client.collections.create(name=name, properties=COLLECTION_PROPERTIES)
        logger.info("Created collection '%s'", name)
    else:
        logger.info("Collection '%s' already exists", name)

    return client.collections.get(name)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def source_hash(md_path: Path) -> str:
    """Return hex SHA-256 over the content file and its companion meta file."""
    h = hashlib.sha256(md_path.read_bytes())
    meta_path = md_path.with_name(md_path.stem + "-meta.yaml")
    if meta_path.exists():
        h.update(meta_path.read_bytes())
    return h.hexdigest()


def load_meta(md_path: Path) -> dict[str, str]:
    """Load companion -meta.yaml for a markdown file.

    Falls back to deriving topic from the parent folder name and
    category from the file stem if no meta file exists.
    """
    meta_path = md_path.with_name(md_path.stem + "-meta.yaml")

    if meta_path.exists():
        with open(meta_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        if not isinstance(data, dict):
            logger.warning("Invalid YAML in %s, falling back to defaults", meta_path)
            data = {}
        return {
            "topic": str(data.get("topic", md_path.parent.name)),
            "category": str(data.get("category", md_path.stem)),
        }

    # Fallback: derive from directory structure
    return {
        "topic": md_path.parent.name,
        "category": md_path.stem,
    }


def chunk_markdown(text: str) -> list[str]:
    """Split markdown text into chunks using header-aware + recursive splitting."""
    md_splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=MD_HEADERS_TO_SPLIT,
        strip_headers=False,
    )
    md_docs = md_splitter.split_text(text)

    char_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
    )
    final_docs = char_splitter.split_documents(md_docs)

    return [doc.page_content for doc in final_docs]


def get_existing_sources(collection: Any) -> dict[str, str]:
    """Fetch all unique (source, source_hash) pairs from the collection."""
    existing: dict[str, str] = {}

    try:
        for obj in collection.iterator(return_properties=["source", "source_hash"]):
            source = obj.properties.get("source", "")
            source_hash = obj.properties.get("source_hash", "")
            if source and source not in existing:
                existing[source] = source_hash
    except Exception as exc:
        logger.warning("Could not fetch existing sources: %s", exc)

    return existing


def delete_by_source(collection: Any, source: str) -> None:
    """Delete all objects with a given source value."""
    collection.data.delete_many(where=Filter.by_property("source").equal(source))


# ---------------------------------------------------------------------------
# Main ingestion
# ---------------------------------------------------------------------------
def ingest() -> None:
    """Run the full ingestion pipeline."""
    # --- Config ---
    collection_name = os.getenv("WEAVIATE_COLLECTION", "SoofiKnowledge")
    embedding_model = os.getenv("EMBEDDING_MODEL")
    if not embedding_model:
        raise RuntimeError(
            "EMBEDDING_MODEL env var required. "
            "Format: 'provider:model-name' e.g. 'openai:text-embedding-3-large'"
        )

    knowledge_dir = Path(os.getenv("KNOWLEDGE_DIR", str(KNOWLEDGE_DIR)))
    if not knowledge_dir.exists():
        raise RuntimeError(f"Knowledge directory not found: {knowledge_dir}")

    # --- Connect ---
    client = connect_weaviate()

    try:
        collection = ensure_collection(client, collection_name)

        # --- Scan content files ---
        content_files = sorted(knowledge_dir.rglob("*.md"))
        if not content_files:
            logger.warning("No markdown files found in %s", knowledge_dir)
            return

        logger.info("Found %d markdown files in %s", len(content_files), knowledge_dir)

        # --- Change detection ---
        existing = get_existing_sources(collection)
        logger.info("Found %d existing sources in Weaviate", len(existing))

        # --- Embeddings ---
        logger.info("Initializing embedding model: %s", embedding_model)
        embeddings = init_embeddings(embedding_model)

        # --- Process files ---
        stats = {"added": 0, "updated": 0, "deleted": 0, "skipped": 0}
        processed_sources: set[str] = set()

        for md_path in content_files:
            source = md_path.relative_to(knowledge_dir).as_posix()
            processed_sources.add(source)
            current_hash = source_hash(md_path)

            # Skip unchanged files
            if source in existing and existing[source] == current_hash:
                logger.debug("Skipping unchanged: %s", source)
                stats["skipped"] += 1
                continue

            # Read and chunk
            text = md_path.read_text(encoding="utf-8")
            chunks = chunk_markdown(text)

            if not chunks:
                logger.warning("No chunks produced for %s", source)
                continue

            # Delete old chunks if updating
            is_update = source in existing
            if is_update:
                logger.info("Updating: %s", source)
                delete_by_source(collection, source)
            else:
                logger.info("Adding: %s", source)

            # Load metadata
            meta = load_meta(md_path)

            # Embed
            vectors = embeddings.embed_documents(chunks)

            # Batch insert
            with collection.batch.dynamic() as batch:
                for chunk_text, vector in zip(chunks, vectors):
                    batch.add_object(
                        properties={
                            "text": chunk_text,
                            "topic": meta["topic"],
                            "category": meta["category"],
                            "source": source,
                            "source_hash": current_hash,
                        },
                        vector=vector,
                    )

            if batch.number_errors > 0:
                logger.error("Batch insert had %d errors for %s", batch.number_errors, source)

            logger.info("Inserted %d chunks for %s", len(chunks), source)
            stats["updated" if is_update else "added"] += 1

        # --- Cleanup deleted files ---
        for source in existing:
            if source not in processed_sources:
                logger.info("Deleting removed source: %s", source)
                delete_by_source(collection, source)
                stats["deleted"] += 1

        # --- Summary ---
        logger.info(
            "Ingestion complete — Added: %d, Updated: %d, Deleted: %d, Skipped: %d",
            stats["added"],
            stats["updated"],
            stats["deleted"],
            stats["skipped"],
        )

    finally:
        client.close()


if __name__ == "__main__":
    ingest()
