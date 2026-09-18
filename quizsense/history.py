"""Session persistence and aggregate latency statistics."""

from __future__ import annotations

import csv
import json
from collections import deque
from pathlib import Path
from statistics import mean

from .models import QAItem


class QAHistory:
    def __init__(self, max_items: int = 100):
        self.items: deque[QAItem] = deque(maxlen=max_items)

    def add(self, item: QAItem) -> None:
        self.items.append(item)

    def summary(self) -> dict[str, float | int]:
        successful = [item for item in self.items if item.status == "ok"]
        return {
            "total_items": len(self.items),
            "successful_items": len(successful),
            "failed_items": len(self.items) - len(successful),
            "mean_stt_latency_ms": (
                round(mean([x.stt_latency_ms for x in successful]), 2) if successful else 0.0
            ),
            "mean_answer_latency_ms": (
                round(mean([x.answer_latency_ms for x in successful]), 2) if successful else 0.0
            ),
            "mean_total_latency_ms": (
                round(mean([x.total_latency_ms for x in successful]), 2) if successful else 0.0
            ),
        }

    def export(self, directory: str | Path, session_id: str) -> tuple[Path, Path]:
        output_dir = Path(directory)
        output_dir.mkdir(parents=True, exist_ok=True)
        json_path = output_dir / f"{session_id}.json"
        csv_path = output_dir / f"{session_id}.csv"
        payload = {
            "session_id": session_id,
            "summary": self.summary(),
            "items": [x.to_dict() for x in self.items],
        }
        json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        fieldnames = list(QAItem.__dataclass_fields__)
        with csv_path.open("w", encoding="utf-8-sig", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(item.to_dict() for item in self.items)
        return json_path, csv_path
