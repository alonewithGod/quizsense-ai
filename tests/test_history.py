import json

from quizsense.history import QAHistory
from quizsense.models import QAItem


def _item(status="ok"):
    return QAItem(1.0, "raw", "question?", "질문?", "answer", "답", 0.8, 100, 200, 300, status)


def test_summary_and_export(tmp_path):
    history = QAHistory()
    history.add(_item())
    history.add(_item("error"))
    assert history.summary()["successful_items"] == 1
    json_path, csv_path = history.export(tmp_path, "session")
    assert csv_path.exists()
    assert json.loads(json_path.read_text(encoding="utf-8"))["summary"]["failed_items"] == 1
