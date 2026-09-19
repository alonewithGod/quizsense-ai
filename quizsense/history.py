"""Session persistence and aggregate latency statistics."""

from __future__ import annotations

import csv
import json
from collections import deque
from pathlib import Path
from statistics import mean, median

from .models import QAItem


class QAHistory:
    def __init__(self, max_items: int = 100):
        self.items: deque[QAItem] = deque(maxlen=max_items)

    def add(self, item: QAItem) -> None:
        self.items.append(item)

    def summary(self) -> dict[str, float | int]:
        successful = [item for item in self.items if item.status == "ok"]
        stt_latencies = [item.stt_latency_ms for item in successful]
        answer_latencies = [item.answer_latency_ms for item in successful]
        total_latencies = [item.total_latency_ms for item in successful]
        return {
            "total_items": len(self.items),
            "successful_items": len(successful),
            "failed_items": len(self.items) - len(successful),
            "mean_stt_latency_ms": self._mean(stt_latencies),
            "median_stt_latency_ms": self._median(stt_latencies),
            "p95_stt_latency_ms": self._percentile(stt_latencies, 95),
            "mean_answer_latency_ms": self._mean(answer_latencies),
            "median_answer_latency_ms": self._median(answer_latencies),
            "p95_answer_latency_ms": self._percentile(answer_latencies, 95),
            "mean_total_latency_ms": self._mean(total_latencies),
            "median_total_latency_ms": self._median(total_latencies),
            "p95_total_latency_ms": self._percentile(total_latencies, 95),
        }

    @staticmethod
    def _mean(values: list[float]) -> float:
        return round(mean(values), 2) if values else 0.0

    @staticmethod
    def _median(values: list[float]) -> float:
        return round(median(values), 2) if values else 0.0

    @staticmethod
    def _percentile(values: list[float], percentile: float) -> float:
        """Return a linearly interpolated percentile without external dependencies."""
        if not values:
            return 0.0
        ordered = sorted(values)
        position = (len(ordered) - 1) * percentile / 100
        lower_index = int(position)
        upper_index = min(lower_index + 1, len(ordered) - 1)
        fraction = position - lower_index
        value = ordered[lower_index] + (ordered[upper_index] - ordered[lower_index]) * fraction
        return round(value, 2)

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
