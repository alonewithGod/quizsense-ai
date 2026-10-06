"""Bridge live application results to reproducible session artifacts."""

from __future__ import annotations

import math
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
        detection_score = self._bounded_score(detection_score)
        stt_latency_ms = self._latency("stt_latency_ms", stt_latency_ms)
        answer_latency_ms = self._latency("answer_latency_ms", answer_latency_ms)
        item = QAItem(
            timestamp=self.clock(),
            transcript=transcript,
            question=question,
            question_ko=question_ko,
            answer_en=answer_en,
            answer_ko=answer_ko,
            detection_score=round(detection_score, 4),
            stt_latency_ms=round(stt_latency_ms, 2),
            answer_latency_ms=round(answer_latency_ms, 2),
            total_latency_ms=round(stt_latency_ms + answer_latency_ms, 2),
            status=status,
            error=error,
        )
        self.history.add(item)
        return item

    @staticmethod
    def _latency(name: str, value: float) -> float:
        numeric = float(value)
        if not math.isfinite(numeric) or numeric < 0:
            raise ValueError(f"{name} must be a finite non-negative number; got {value!r}")
        return numeric

    @staticmethod
    def _bounded_score(value: float) -> float:
        numeric = float(value)
        if not math.isfinite(numeric) or not 0 <= numeric <= 1:
            raise ValueError(f"detection_score must be between 0 and 1; got {value!r}")
        return numeric

    def export(self, directory: str | Path, session_id: str) -> tuple[Path, Path]:
        return self.history.export(directory, session_id)
