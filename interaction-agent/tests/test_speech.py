"""Tests for speech text helpers."""

from src.speech import (
    generate_speech_text,
    generate_trailing_question_speech_text,
    generate_transition_speech_text,
    normalize_speech_for_dedup,
)


def test_short_opener_concatenates_with_next_sentence_at_stream_end():
    # "Das klingt gut!" (15 chars) alone is below min-length. At stream end
    # the next sentence must be appended so TTS actually speaks something.
    text = (
        "Das klingt gut! Für den Anwendungsfall Engineering-Copilot müssen wir "
        "nun den nächsten Schritt gehen."
    )
    result = generate_speech_text(text, streaming=False)
    assert result.startswith("Das klingt gut!")
    assert "Engineering-Copilot" in result


def test_short_opener_during_streaming_holds_back():
    # During streaming a short opener must NOT be emitted — the follow-up may
    # still be on its way.
    text = "Kein Problem!"
    assert generate_speech_text(text, streaming=True) == ""


def test_only_short_opener_at_stream_end_stays_empty():
    # If the whole response is a short opener, there's nothing meaningful to say.
    assert generate_speech_text("Kein Problem!", streaming=False) == ""


def test_transition_plain_question():
    assert (
        generate_transition_speech_text("Welchen dieser Datensätze möchtest du verwenden?")
        == "Welchen dieser Datensätze möchtest du verwenden?"
    )


def test_transition_strips_markdown_and_links():
    text = "Möchtest du **jetzt** [diesen Datensatz](https://hf.co/foo) verwenden?"
    assert (
        generate_transition_speech_text(text)
        == "Möchtest du jetzt diesen Datensatz verwenden?"
    )


def test_transition_strips_leading_newlines():
    assert (
        generate_transition_speech_text("\n\nSoll ich das Training starten?")
        == "Soll ich das Training starten?"
    )


def test_transition_empty_input():
    assert generate_transition_speech_text("") == ""
    assert generate_transition_speech_text("   \n\n  ") == ""


def test_transition_trailing_period_stripped():
    assert generate_transition_speech_text("Das ist der nächste Schritt.") == "Das ist der nächste Schritt"


def test_trailing_question_extracts_final_sentence():
    text = (
        "Hier sind 3 Datensätze, die passen könnten.\n\n"
        "- Dataset A\n- Dataset B\n\n"
        "Welchen dieser Datensätze möchtest du verwenden?"
    )
    assert (
        generate_trailing_question_speech_text(text)
        == "Welchen dieser Datensätze möchtest du verwenden?"
    )


def test_trailing_question_returns_empty_when_no_question():
    assert generate_trailing_question_speech_text("Das war's. Fertig.") == ""


def test_trailing_question_strips_markdown():
    text = "Ich habe alles geprüft. Soll ich den **[Datensatz](https://hf.co/x)** laden?"
    assert (
        generate_trailing_question_speech_text(text)
        == "Soll ich den Datensatz laden?"
    )


def test_trailing_question_dedup_normalization():
    # Loose containment: same sentence, one clip already contains it.
    trailing = "Soll ich nach passenden Datensätzen suchen?"
    emitted = "Kurze Einleitung. Soll ich nach passenden Datensätzen suchen?"
    assert normalize_speech_for_dedup(trailing) in normalize_speech_for_dedup(emitted)


def test_trailing_question_dedup_treats_different_questions_as_new():
    trailing = "Welchen Datensatz möchtest du?"
    emitted = "Das sind die Ergebnisse der Suche"
    assert normalize_speech_for_dedup(trailing) not in normalize_speech_for_dedup(emitted)
