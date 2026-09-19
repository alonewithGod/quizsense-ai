import json

from quizsense.history import QAHistory
from quizsense.models import QAItem


def _item(status="ok", stt=100, answer=200, total=300):
    return QAItem(
        1.0,
        "raw",
        "question?",
        "질문?",
        "answer",
        "답",
        0.8,
        stt,
        answer,
        total,
        status,
    )


def test_summary_and_export(tmp_path):
    history = QAHistory()
    history.add(_item())
    history.add(_item("error"))
    assert history.summary()["successful_items"] == 1
    json_path, csv_path = history.export(tmp_path, "session")
    assert csv_path.exists()
    assert json.loads(json_path.read_text(encoding="utf-8"))["summary"]["failed_items"] == 1


def test_summary_includes_median_and_p95_for_successful_items_only():
    history = QAHistory()
    history.add(_item(stt=100, answer=200, total=300))
    history.add(_item(stt=200, answer=400, total=600))
    history.add(_item(stt=300, answer=600, total=900))
    history.add(_item(status="error", stt=9000, answer=9000, total=18000))

    summary = history.summary()

    assert summary["median_stt_latency_ms"] == 200
    assert summary["p95_stt_latency_ms"] == 290
    assert summary["median_answer_latency_ms"] == 400
    assert summary["p95_answer_latency_ms"] == 580
    assert summary["median_total_latency_ms"] == 600
    assert summary["p95_total_latency_ms"] == 870


def test_empty_summary_has_zero_latency_statistics():
    summary = QAHistory().summary()

    assert summary["median_total_latency_ms"] == 0.0
    assert summary["p95_total_latency_ms"] == 0.0
