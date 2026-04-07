"""Tests for session_logger.py — pure function tests, no external deps."""

from pathlib import Path

import pytest

from src.friction import detect_friction as _detect_friction


# ---------------------------------------------------------------------------
# Friction detection tests
# ---------------------------------------------------------------------------


class TestFrictionDetection:
    def test_correction_german_nein(self) -> None:
        result = _detect_friction("Nein, ich meine Textklassifikation.")
        assert result is not None
        assert result[0] == "correction"
        assert result[1] == "low"

    def test_correction_german_falsch(self) -> None:
        result = _detect_friction("Das ist falsch, ich wollte RAG.")
        assert result is not None
        assert result[0] == "correction"

    def test_correction_english(self) -> None:
        result = _detect_friction("No, that's not what I meant.")
        assert result is not None
        assert result[0] == "correction"

    def test_correction_i_mean(self) -> None:
        result = _detect_friction("I mean the text classification task.")
        assert result is not None
        assert result[0] == "correction"

    def test_clarification_request(self) -> None:
        result = _detect_friction("Ich verstehe nicht was Sie meinen.")
        assert result is not None
        assert result[0] == "clarification_request"

    def test_incomplete_answer(self) -> None:
        result = _detect_friction("Und was ist mit der Datenmenge?")
        assert result is not None
        assert result[0] == "incomplete_answer"

    def test_no_friction_normal_message(self) -> None:
        assert _detect_friction("Ich möchte ein Modell fine-tunen.") is None

    def test_no_friction_question(self) -> None:
        assert _detect_friction("Welche Datenmenge brauche ich?") is None

    def test_no_friction_empty(self) -> None:
        assert _detect_friction("") is None

    # -- neue Patterns (aus realem Session-Log abgeleitet) -------------------

    def test_correction_nee(self) -> None:
        result = _detect_friction("Nee, ich meinte die jetzige 2026.")
        assert result is not None
        assert result[0] == "correction"

    def test_correction_ich_meinte(self) -> None:
        result = _detect_friction("Ich meinte eigentlich Fine-Tuning, nicht RAG.")
        assert result is not None
        assert result[0] == "correction"

    def test_correction_i_meant(self) -> None:
        result = _detect_friction("I meant the 2026 edition.")
        assert result is not None
        assert result[0] == "correction"

    def test_incomplete_answer_da_fehlt(self) -> None:
        result = _detect_friction("Naja, aber da fehlt ja noch Pre-Training.")
        assert result is not None
        assert result[0] == "incomplete_answer"

    def test_incomplete_answer_naja(self) -> None:
        result = _detect_friction("Naja, das war nur Fine-Tuning.")
        assert result is not None
        assert result[0] == "incomplete_answer"

    def test_unexpected_behavior_haefte_erwartet(self) -> None:
        result = _detect_friction(
            "Ich hätte jetzt erwartet, dass du die Ansicht schließt."
        )
        assert result is not None
        assert result[0] == "unexpected_behavior"

    def test_unexpected_behavior_warum_nicht(self) -> None:
        result = _detect_friction("Warum hast du das nicht gemacht?")
        assert result is not None
        assert result[0] == "unexpected_behavior"


# ---------------------------------------------------------------------------
# SessionLogger file I/O tests
# ---------------------------------------------------------------------------

# Import here — module-level constants are set once, log_dir is passed per-instance
from src.session_logger import SessionLogger, get_or_create_logger  # noqa: E402


class TestSessionLogger:
    def test_file_created_immediately(self, tmp_path: Path) -> None:
        sl = SessionLogger("test-session-001", language="de", log_dir=tmp_path)
        files = list(tmp_path.glob("*.md"))
        assert len(files) == 1
        content = files[0].read_text(encoding="utf-8")
        assert "# Soofi Session" in content
        assert "## Log" in content

    def test_user_message_appended(self, tmp_path: Path) -> None:
        sl = SessionLogger("test-session-002", language="de", log_dir=tmp_path)
        sl.log_user_message("Ich möchte fine-tunen.")
        content = sl._path.read_text(encoding="utf-8")
        assert "Ich möchte fine-tunen." in content
        assert "type:user" in content

    def test_friction_event_annotated(self, tmp_path: Path) -> None:
        sl = SessionLogger("test-session-003", language="de", log_dir=tmp_path)
        sl.log_user_message("Nein, ich meine Textklassifikation.")
        content = sl._path.read_text(encoding="utf-8")
        assert "type:friction" in content
        assert "subtype:correction" in content
        assert "confidence:low" in content
        assert sl._friction_events == 1

    def test_tool_call_logged(self, tmp_path: Path) -> None:
        sl = SessionLogger("test-session-004", language="de", log_dir=tmp_path)
        sl.log_tool_call("ask_advisor_tool", "Fine-Tuning Klassifikation")
        content = sl._path.read_text(encoding="utf-8")
        assert "type:tool_call" in content
        assert "ask_advisor" in content
        assert "Fine-Tuning Klassifikation" in content
        assert sl._advisor_calls == 1

    def test_rag_sources_logged(self, tmp_path: Path) -> None:
        sl = SessionLogger("test-session-005", language="de", log_dir=tmp_path)
        sources = [
            {"file": "guide.pdf", "section": "Methodik", "score": 0.91},
            {"file": "data.pdf", "section": "Überblick", "score": 0.87},
        ]
        sl.log_rag_sources(sources)
        content = sl._path.read_text(encoding="utf-8")
        assert "type:rag_sources" in content
        assert "guide.pdf" in content
        assert "0.91" in content
        assert sl._rag_sources_total == 2

    def test_finalize_prepends_frontmatter(self, tmp_path: Path) -> None:
        sl = SessionLogger("test-session-006", language="de", log_dir=tmp_path)
        sl.log_user_message("Hallo Soofi.")
        sl.log_agent_response("Hallo! Wie kann ich helfen?")
        sl.finalize("normal")
        content = sl._path.read_text(encoding="utf-8")
        assert content.startswith("---\n")
        assert "session_id: test-session-006" in content
        assert "end_reason: normal" in content
        assert "language: de" in content
        assert "message_count: 1" in content
        assert "## Log" in content
        assert "## Metadata" in content

    def test_recommendation_detected_lora(self, tmp_path: Path) -> None:
        sl = SessionLogger("test-session-007", language="de", log_dir=tmp_path)
        sl.log_agent_response("Ich empfehle LoRA Fine-Tuning für Ihren Anwendungsfall.")
        assert sl._recommendation == "lora_finetuning"

    def test_recommendation_detected_qlora(self, tmp_path: Path) -> None:
        sl = SessionLogger("test-session-008", language="de", log_dir=tmp_path)
        sl.log_agent_response("QLoRA ist für Ihren Fall ideal.")
        assert sl._recommendation == "qlora"

    def test_recommendation_not_overwritten(self, tmp_path: Path) -> None:
        sl = SessionLogger("test-session-009", language="de", log_dir=tmp_path)
        sl.log_agent_response("LoRA ist empfohlen.")
        sl.log_agent_response("RAG könnte auch nützlich sein.")
        # First detection wins
        assert sl._recommendation == "lora_finetuning"

    def test_training_started_logged(self, tmp_path: Path) -> None:
        sl = SessionLogger("test-session-010", language="de", log_dir=tmp_path)
        sl.log_training_started("job-abc123")
        content = sl._path.read_text(encoding="utf-8")
        assert "type:training_started" in content
        assert "job-abc123" in content
        assert sl._training_started is True

    def test_latency_recorded(self, tmp_path: Path) -> None:
        sl = SessionLogger("test-session-011", language="de", log_dir=tmp_path)
        sl.log_user_message("Hallo.")
        sl.log_agent_response("Antwort.")
        content = sl._path.read_text(encoding="utf-8")
        assert "latency_ms:" in content

    def test_get_or_create_returns_same_instance(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        import src.session_logger as sl_mod
        monkeypatch.setattr(sl_mod, "SESSION_LOG_DIR", tmp_path)
        monkeypatch.setattr(sl_mod, "SESSION_LOG_ENABLED", True)
        monkeypatch.setattr(sl_mod, "_sessions", type(sl_mod._sessions)())

        sl1 = sl_mod.get_or_create_logger("same-session", "de")
        sl2 = sl_mod.get_or_create_logger("same-session", "de")
        assert sl1 is sl2

    def test_logging_disabled_returns_none(self, monkeypatch: pytest.MonkeyPatch) -> None:
        import src.session_logger as sl_mod
        monkeypatch.setattr(sl_mod, "SESSION_LOG_ENABLED", False)
        result = sl_mod.get_or_create_logger("any-session", "de")
        assert result is None
