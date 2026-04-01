"""Tests for RAG source deduplication logic in a2a_handler.py."""

import pytest


def deduplicate_sources(results: list[dict]) -> list[dict]:
    """Extract and deduplicate sources from search results.

    Mirrors the deduplication logic in AdvisorAgentExecutor.execute().
    """
    seen: dict[tuple[str, str], int] = {}
    sources: list[dict] = []
    for r in results:
        score = r.get("reranker_score")
        if score is None:
            continue
        file = r.get("source_file", "")
        section = r.get("section_title", "")
        key = (file, section)
        if key in seen:
            prev_idx = seen[key]
            if score > sources[prev_idx]["score"]:
                sources[prev_idx] = {
                    "file": file,
                    "section": section,
                    "score": score,
                    "url": r.get("metadata", {}).get("source", ""),
                }
            continue
        seen[key] = len(sources)
        sources.append(
            {
                "file": file,
                "section": section,
                "score": score,
                "url": r.get("metadata", {}).get("source", ""),
            }
        )
    return sources


class TestDeduplication:
    def test_no_duplicates(self) -> None:
        results = [
            {"source_file": "a.md", "section_title": "S1", "reranker_score": 0.9, "metadata": {"source": "/docs/a.md"}},
            {"source_file": "b.md", "section_title": "S2", "reranker_score": 0.8, "metadata": {"source": "/docs/b.md"}},
        ]
        sources = deduplicate_sources(results)
        assert len(sources) == 2

    def test_duplicate_keeps_higher_score(self) -> None:
        results = [
            {"source_file": "a.md", "section_title": "S1", "reranker_score": 0.7, "metadata": {"source": "/docs/a.md"}},
            {"source_file": "a.md", "section_title": "S1", "reranker_score": 0.9, "metadata": {"source": "/docs/a.md"}},
        ]
        sources = deduplicate_sources(results)
        assert len(sources) == 1
        assert sources[0]["score"] == 0.9

    def test_duplicate_keeps_first_when_higher(self) -> None:
        results = [
            {"source_file": "a.md", "section_title": "S1", "reranker_score": 0.9, "metadata": {"source": "/docs/a.md"}},
            {"source_file": "a.md", "section_title": "S1", "reranker_score": 0.7, "metadata": {"source": "/docs/a.md"}},
        ]
        sources = deduplicate_sources(results)
        assert len(sources) == 1
        assert sources[0]["score"] == 0.9

    def test_same_file_different_sections(self) -> None:
        results = [
            {"source_file": "a.md", "section_title": "S1", "reranker_score": 0.9, "metadata": {"source": "/docs/a.md#s1"}},
            {"source_file": "a.md", "section_title": "S2", "reranker_score": 0.8, "metadata": {"source": "/docs/a.md#s2"}},
        ]
        sources = deduplicate_sources(results)
        assert len(sources) == 2

    def test_skips_results_without_reranker_score(self) -> None:
        results = [
            {"source_file": "a.md", "section_title": "S1", "metadata": {"source": "/docs/a.md"}},
            {"source_file": "b.md", "section_title": "S2", "reranker_score": 0.8, "metadata": {"source": "/docs/b.md"}},
        ]
        sources = deduplicate_sources(results)
        assert len(sources) == 1
        assert sources[0]["file"] == "b.md"

    def test_empty_results(self) -> None:
        assert deduplicate_sources([]) == []

    def test_three_duplicates(self) -> None:
        results = [
            {"source_file": "a.md", "section_title": "S1", "reranker_score": 0.5, "metadata": {"source": "/docs/a.md"}},
            {"source_file": "a.md", "section_title": "S1", "reranker_score": 0.9, "metadata": {"source": "/docs/a.md"}},
            {"source_file": "a.md", "section_title": "S1", "reranker_score": 0.7, "metadata": {"source": "/docs/a.md"}},
        ]
        sources = deduplicate_sources(results)
        assert len(sources) == 1
        assert sources[0]["score"] == 0.9
