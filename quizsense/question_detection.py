"""Explainable Korean/English question detection."""

from __future__ import annotations

import re
import time
from collections import deque
from difflib import SequenceMatcher

from .models import QuestionDecision


class QuestionDetector:
    EN_STARTERS = {
        "what", "why", "how", "when", "where", "who", "which", "whose", "whom",
        "can", "could", "would", "should", "is", "are", "am", "do", "does", "did",
        "will", "may", "has", "have", "had",
    }
    EN_HINTS = (
        "question for you", "can anyone tell me", "what do you think", "who can",
        "why do you think", "how would you", "please explain",
    )
    KO_ENDINGS = (
        "인가요", "일까요", "나요", "까요", "습니까", "나요", "거죠", "건가요",
        "뭔가요", "무엇인가", "왜", "어떻게", "누가", "언제", "어디",
    )
    KO_HINTS = (
        "질문입니다", "질문할게", "설명해 주세요", "설명해주세요", "답해 보세요",
        "누가 말해볼까요", "무슨 뜻", "알고 있나요",
    )
    KO_STARTERS = ("왜 ", "어떻게 ", "무엇", "뭐", "누가 ", "언제 ", "어디")

    def __init__(self, cooldown_sec: float = 5.0, duplicate_window_sec: float = 30.0):
        self.cooldown_sec = cooldown_sec
        self.duplicate_window_sec = duplicate_window_sec
        self._last_trigger = 0.0
        self._recent: deque[tuple[float, str]] = deque(maxlen=20)

    @staticmethod
    def normalize(text: str) -> str:
        return re.sub(r"\s+", " ", text).strip()

    def classify(self, text: str) -> QuestionDecision:
        normalized = self.normalize(text)
        lowered = normalized.lower()
        reasons: list[str] = []
        score = 0.0
        words = re.findall(r"[A-Za-z']+", lowered)

        if not normalized:
            return QuestionDecision(False, 0.0, ("empty",), "")
        if "?" in normalized:
            score += 0.65
            reasons.append("question_mark")
        if words and words[0] in self.EN_STARTERS and len(words) >= 3:
            score += 0.45
            reasons.append("english_starter")
        if any(hint in lowered for hint in self.EN_HINTS):
            score += 0.55
            reasons.append("english_prompt_hint")
        if any(hint in normalized for hint in self.KO_HINTS):
            score += 0.6
            reasons.append("korean_prompt_hint")
        if normalized.startswith(self.KO_STARTERS):
            score += 0.5
            reasons.append("korean_starter")
        if any(normalized.rstrip("?.! ").endswith(ending) for ending in self.KO_ENDINGS):
            score += 0.5
            reasons.append("korean_question_ending")
        if len(normalized) < 4:
            score -= 0.3
            reasons.append("too_short")

        extracted = self.extract(normalized) if score >= 0.45 else ""
        return QuestionDecision(score >= 0.45, min(max(score, 0.0), 1.0), tuple(reasons), extracted)

    def should_trigger(self, text: str, now: float | None = None) -> QuestionDecision:
        decision = self.classify(text)
        if not decision.is_question:
            return decision
        current = time.time() if now is None else now
        self._evict_recent(current)
        if current - self._last_trigger < self.cooldown_sec:
            return QuestionDecision(
                False, decision.score, decision.reasons + ("cooldown",), decision.extracted_question
            )
        duplicate = any(
            SequenceMatcher(None, decision.extracted_question.lower(), old.lower()).ratio() >= 0.9
            for _, old in self._recent
        )
        if duplicate:
            return QuestionDecision(
                False, decision.score, decision.reasons + ("duplicate",), decision.extracted_question
            )
        self._last_trigger = current
        self._recent.append((current, decision.extracted_question))
        return decision

    def _evict_recent(self, now: float) -> None:
        while self._recent and now - self._recent[0][0] > self.duplicate_window_sec:
            self._recent.popleft()

    def extract(self, text: str) -> str:
        normalized = self.normalize(text)
        parts = [p.strip() for p in re.split(r"(?<=[?.!])\s+", normalized) if p.strip()]
        candidates = [p for p in parts if self.classify_fragment(p)]
        selected = candidates[-1] if candidates else normalized
        selected = re.sub(r"^(so|now|okay|ok|well|then|and|but)\s+", "", selected, flags=re.I)
        return selected if selected.endswith("?") else selected + "?"

    def classify_fragment(self, text: str) -> bool:
        lowered = text.lower()
        words = re.findall(r"[A-Za-z']+", lowered)
        return (
            "?" in text
            or (words and words[0] in self.EN_STARTERS and len(words) >= 3)
            or any(h in lowered for h in self.EN_HINTS)
            or any(h in text for h in self.KO_HINTS)
            or text.startswith(self.KO_STARTERS)
            or any(text.rstrip("?.! ").endswith(e) for e in self.KO_ENDINGS)
        )
