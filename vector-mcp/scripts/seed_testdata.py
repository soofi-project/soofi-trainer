"""Seed Weaviate with test documents for development."""

import os
import weaviate
from weaviate.classes.config import DataType, Property
from langchain.embeddings.base import init_embeddings

DOCS = [
    {
        "text": "RAG (Retrieval-Augmented Generation) is ideal when you need to query large, frequently updated knowledge bases. It avoids the cost and complexity of fine-tuning while providing accurate, grounded responses.",
        "topic": "rag",
        "category": "best_practice",
        "source": "soofi_kb",
    },
    {
        "text": "When choosing an embedding model for RAG, consider the trade-off between quality and cost. OpenAI text-embedding-3-large offers high quality, while smaller models like text-embedding-3-small are more cost-effective for large-scale applications.",
        "topic": "rag",
        "category": "best_practice",
        "source": "soofi_kb",
    },
    {
        "text": "A common RAG pitfall is poor chunk sizing. Too small chunks lose context, too large chunks dilute relevance. Typical sweet spot is 256-512 tokens with overlap.",
        "topic": "rag",
        "category": "pitfall",
        "source": "soofi_kb",
    },
    {
        "text": "Fine-tuning is recommended when you need to adapt the model behavior, tone, or domain-specific reasoning. It works best with high-quality, curated training data of at least a few hundred examples.",
        "topic": "fine_tuning",
        "category": "best_practice",
        "source": "soofi_kb",
    },
    {
        "text": "A common pitfall in fine-tuning is overfitting on small datasets. Always hold out a validation set and monitor loss curves during training.",
        "topic": "fine_tuning",
        "category": "pitfall",
        "source": "soofi_kb",
    },
    {
        "text": "Quantization (e.g. GPTQ, AWQ, GGUF) reduces model size and inference cost with minimal quality loss. It is essential for deploying large models on consumer hardware.",
        "topic": "quantization",
        "category": "use_case",
        "source": "soofi_kb",
    },
]


def main():
    collection_name = os.getenv("WEAVIATE_COLLECTION", "SoofiKnowledge")

    client = weaviate.connect_to_local(
        host=os.getenv("WEAVIATE_HOST", "weaviate"),
        port=int(os.getenv("WEAVIATE_PORT", "8080")),
    )

    # Create collection if it doesn't exist
    if not client.collections.exists(collection_name):
        client.collections.create(
            name=collection_name,
            properties=[
                Property(name="text", data_type=DataType.TEXT),
                Property(name="topic", data_type=DataType.TEXT),
                Property(name="category", data_type=DataType.TEXT),
                Property(name="source", data_type=DataType.TEXT),
            ],
        )
        print(f"Created collection '{collection_name}'")
    else:
        print(f"Collection '{collection_name}' already exists")

    # Generate embeddings
    embeddings = init_embeddings(os.environ["EMBEDDING_MODEL"])
    vectors = embeddings.embed_documents([d["text"] for d in DOCS])
    print(f"Generated {len(vectors)} embeddings ({len(vectors[0])} dimensions)")

    # Insert documents
    collection = client.collections.get(collection_name)
    with collection.batch.dynamic() as batch:
        for doc, vec in zip(DOCS, vectors):
            batch.add_object(properties=doc, vector=vec)

    print(f"Inserted {len(DOCS)} test documents")
    client.close()


if __name__ == "__main__":
    main()
