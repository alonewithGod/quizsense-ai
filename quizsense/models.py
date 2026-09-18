"""Domain models shared by the application and evaluation tools."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class TranscriptChunk:
    timestamp: float
    text: str


@dataclass(frozen=True)
class QuestionDecision:
    is_question: bool
    score: float
    reasons: tuple[str, ...]
    extracted_question: str


@dataclass(frozen=True)
class QAItem:
    timestamp: float
    transcript: str
    question: str
    question_ko: str
    answer_en: str
    answer_ko: str
    detection_score: float
    stt_latency_ms: float
    answer_latency_ms: float
    total_latency_ms: float
    status: str = "ok"
    error: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
