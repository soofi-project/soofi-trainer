"""MCP server for searching datasets on HuggingFace Hub."""

import logging
import os
import threading
import time
from datetime import datetime
from fnmatch import fnmatch
from typing import Any

import uvicorn
from fastmcp import FastMCP
from huggingface_hub import HfApi

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

mcp = FastMCP("soofi-huggingface-mcp")

_api = HfApi()
_rate_lock = threading.Lock()
_last_request_ts = 0.0

_TASK_MAPPING: dict[str, list[str]] = {
    "question-answering": ["question-answering", "extractive-qa", "open-domain-qa"],
    "summarization": ["summarization", "text2text-generation"],
    "classification": ["text-classification", "sentiment-analysis"],
    "ner": ["token-classification", "named-entity-recognition"],
    "text-generation": ["text-generation", "language-modeling"],
    "translation": ["translation", "machine-translation"],
}

_LICENSE_MAPPING: dict[str, list[str]] = {
    "permissive": ["mit", "apache-2.0", "bsd-*", "cc-by-*", "cc0", "unlicense"],
    "copyleft": ["gpl-*", "lgpl-*", "agpl-*", "cc-by-sa*"],
    "research-only": ["research", "non-commercial", "academic"],
    "commercial": ["mit", "apache-2.0", "bsd-*", "cc0", "openrail"],
}


def _normalize_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip().lower()


def _normalize_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [_normalize_text(value)]
    if isinstance(value, list):
        return [_normalize_text(item) for item in value if item is not None]
    return [_normalize_text(value)]


def _match_pattern(value: str, patterns: list[str]) -> bool:
    return any(fnmatch(value, pattern) for pattern in patterns)


def _license_matches(license_value: Any, license_filter: str | None) -> bool:
    if not license_filter:
        return True
    candidates = _normalize_list(license_value)
    if not candidates:
        return False

    mapped = _LICENSE_MAPPING.get(_normalize_text(license_filter), [_normalize_text(license_filter)])
    for candidate in candidates:
        if _match_pattern(candidate, mapped):
            return True
    return False


def _task_matches(task_value: Any, task_filter: str | None) -> bool:
    if not task_filter:
        return True
    candidates = _normalize_list(task_value)
    if not candidates:
        return False

    mapped = _TASK_MAPPING.get(_normalize_text(task_filter), [_normalize_text(task_filter)])
    for candidate in candidates:
        if _match_pattern(candidate, mapped):
            return True
    return False


def _language_matches(language_value: Any, language_filter: str | None) -> bool:
    if not language_filter:
        return True
    requested = _normalize_text(language_filter)
    candidates = _normalize_list(language_value)
    if not candidates:
        return False

    if requested in {"multi", "multilingual"}:
        return any("multilingual" in cand or cand == "multi" for cand in candidates)
    return any(cand == requested for cand in candidates)


def _as_int(value: Any, default: int = 0) -> int:
    try:
        if value is None:
            return default
        return int(value)
    except (TypeError, ValueError):
        return default


def _extract_size(card_data: dict[str, Any]) -> int | None:
    for key in (
        "dataset_size",
        "num_rows",
        "train_size",
        "size",
    ):
        value = card_data.get(key)
        if isinstance(value, int):
            return value
        if isinstance(value, str) and value.isdigit():
            return int(value)
    return None


def _parse_datetime_iso(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.isoformat()
    text = str(value).strip()
    return text or None


def _respect_rate_limit() -> None:
    global _last_request_ts
    min_interval = float(os.getenv("HF_MIN_REQUEST_INTERVAL", "0.8"))
    if min_interval <= 0:
        return
    with _rate_lock:
        now = time.monotonic()
        wait_for = min_interval - (now - _last_request_ts)
        if wait_for > 0:
            time.sleep(wait_for)
            now = time.monotonic()
        _last_request_ts = now


@mcp.tool()
def search_huggingface_datasets(
    query: str,
    domain: str | None = None,
    task: str | None = None,
    language: str | None = None,
    license: str | None = None,
    min_size: int | None = None,
    max_size: int | None = None,
    limit: int = 10,
) -> dict[str, Any]:
    """Search public datasets on HuggingFace Hub with optional filters.

    Returns datasets sorted by downloads (descending).
    """
    if not query or not query.strip():
        return {"query": query, "total": 0, "results": [], "error": "Query must not be empty."}

    safe_limit = min(max(limit, 1), 50)
    api_limit = min(max(safe_limit * 5, 20), 200)

    try:
        _respect_rate_limit()

        infos = _api.list_datasets(search=query.strip(), limit=api_limit, full=True)

        results: list[dict[str, Any]] = []
        for info in infos:
            card_data = info.cardData if isinstance(info.cardData, dict) else {}

            license_value = card_data.get("license") or info.cardData.get("license") if info.cardData else None
            language_value = card_data.get("language")
            task_value = card_data.get("task_categories") or card_data.get("task_ids")

            if domain:
                domain_text = _normalize_text(domain)
                haystack = " ".join(
                    [
                        _normalize_text(info.id),
                        _normalize_text(info.description),
                        _normalize_text(card_data.get("pretty_name")),
                        _normalize_text(card_data.get("dataset_summary")),
                        " ".join(_normalize_list(card_data.get("tags"))),
                    ]
                )
                if domain_text and domain_text not in haystack:
                    continue

            if not _task_matches(task_value, task):
                continue
            if not _language_matches(language_value, language):
                continue
            if not _license_matches(license_value, license):
                continue

            size = _extract_size(card_data)
            if min_size is not None and (size is None or size < min_size):
                continue
            if max_size is not None and (size is None or size > max_size):
                continue

            downloads = _as_int(getattr(info, "downloads", 0))
            likes = _as_int(getattr(info, "likes", 0))
            info_id = getattr(info, "id", "")

            results.append(
                {
                    "name": info_id,
                    "author": info_id.split("/")[0] if "/" in info_id else None,
                    "description": getattr(info, "description", None)
                    or card_data.get("pretty_name")
                    or card_data.get("dataset_summary"),
                    "size": size,
                    "license": license_value,
                    "languages": _normalize_list(language_value),
                    "tasks": _normalize_list(task_value),
                    "downloads": downloads,
                    "likes": likes,
                    "url": f"https://huggingface.co/datasets/{info_id}" if info_id else None,
                    "last_modified": _parse_datetime_iso(getattr(info, "lastModified", None)),
                }
            )

        results.sort(key=lambda item: item.get("downloads", 0), reverse=True)

        return {
            "query": query,
            "filters": {
                "domain": domain,
                "task": task,
                "language": language,
                "license": license,
                "min_size": min_size,
                "max_size": max_size,
                "limit": safe_limit,
            },
            "total": len(results[:safe_limit]),
            "results": results[:safe_limit],
        }
    except Exception as exc:
        logger.exception("HuggingFace dataset search failed")
        return {
            "query": query,
            "total": 0,
            "results": [],
            "error": str(exc),
        }


def main() -> None:
    app = mcp.http_app()
    port = int(os.getenv("MCP_SERVER_PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")


if __name__ == "__main__":
    main()
