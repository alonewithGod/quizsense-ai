import json

import pytest

from quizsense.session import SessionRecorder


def test_recorder_persists_live_latency_and_summary(tmp_path):
    recorder = SessionRecorder(clock=lambda: 1234.5)
    item = recorder.record(
        transcript="Why does caching reduce latency?",
        question="Why does caching reduce latency?",
        question_ko="캐싱은 왜 지연시간을 줄이나요?",
        answer_en="It avoids repeated work.",
        answer_ko="반복 작업을 피하기 때문입니다.",
        detection_score=0.87555,
        stt_latency_ms=125.678,
        answer_latency_ms=900.126,
    )

    assert item.timestamp == 1234.5
    assert item.detection_score == 0.8756
    assert item.stt_latency_ms == 125.68
    assert item.answer_latency_ms == 900.13
    assert item.total_latency_ms == 1025.8

    json_path, csv_path = recorder.export(tmp_path, "live-session")
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert csv_path.exists()
    assert payload["summary"]["mean_total_latency_ms"] == 1025.8
    assert payload["items"][0]["question"] == "Why does caching reduce latency?"


def test_recorder_excludes_failed_answers_from_latency_summary():
    recorder = SessionRecorder()
    recorder.record(
        transcript="What is a process?",
        question="What is a process?",
        question_ko="",
        answer_en="",
        answer_ko="",
        detection_score=0.8,
        stt_latency_ms=100,
        answer_latency_ms=500,
        status="error",
        error="Ollama unavailable",
    )

    summary = recorder.history.summary()
    assert summary["failed_items"] == 1
    assert summary["mean_total_latency_ms"] == 0.0


def test_recorder_rejects_invalid_latency_measurements():
    recorder = SessionRecorder()
    common = {
        "transcript": "What is caching?",
        "question": "What is caching?",
        "question_ko": "캐싱이 무엇인가요?",
        "answer_en": "It stores reusable data.",
        "answer_ko": "재사용할 데이터를 저장합니다.",
        "detection_score": 0.8,
    }

    for field, stt, answer in (
        ("stt_latency_ms", float("nan"), 100),
        ("answer_latency_ms", 100, float("inf")),
        ("stt_latency_ms", -0.01, 100),
    ):
        with pytest.raises(ValueError, match=field):
            recorder.record(**common, stt_latency_ms=stt, answer_latency_ms=answer)

    assert recorder.history.summary()["total_items"] == 0


def test_recorder_rejects_invalid_detection_scores():
    recorder = SessionRecorder()

    for score in (-0.01, 1.01, float("nan")):
        with pytest.raises(ValueError, match="detection_score must be between 0 and 1"):
            recorder.record(
                transcript="What is caching?",
                question="What is caching?",
                question_ko="캐싱이 무엇인가요?",
                answer_en="It stores reusable data.",
                answer_ko="재사용할 데이터를 저장합니다.",
                detection_score=score,
                stt_latency_ms=100,
                answer_latency_ms=200,
            )

    assert recorder.history.summary()["total_items"] == 0
