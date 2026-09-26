"""Bridge live application results to reproducible session artifacts."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Callable

from .history import QAHistory
from .models import QAItem


class SessionRecorder:
    def __init__(
        self,
        max_items: int = 100,
        clock: Callable[[], float] = time.time,
    ):
        self.history = QAHistory(max_items=max_items)
        self.clock = clock

    def record(
        self,
        *,
        transcript: str,
        question: str,
        question_ko: str,
        answer_en: str,
        answer_ko: str,
        detection_score: float,
        stt_latency_ms: float,
        answer_latency_ms: float,
        status: str = "ok",
        error: str = "",
    ) -> QAItem:
        item = QAItem(
            timestamp=self.clock(),
            transcript=transcript,
            question=question,
            question_ko=question_ko,
            answer_en=answer_en,
            answer_ko=answer_ko,
            detection_score=round(detection_score, 4),
            stt_latency_ms=round(max(0.0, stt_latency_ms), 2),
            answer_latency_ms=round(max(0.0, answer_latency_ms), 2),
            total_latency_ms=round(max(0.0, stt_latency_ms) + max(0.0, answer_latency_ms), 2),
            status=status,
            error=error,
        )
        self.history.add(item)
        return item

    def export(self, directory: str | Path, session_id: str) -> tuple[Path, Path]:
        return self.history.export(directory, session_id)
