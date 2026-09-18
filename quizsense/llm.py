"""Ollama client with strict output validation and actionable errors."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass

import requests


class LLMUnavailableError(RuntimeError):
    pass


@dataclass(frozen=True)
class AnswerPackage:
    question_ko: str
    answer_en: str
    answer_ko: str


class OllamaClient:
    def __init__(self, url: str, model: str, timeout_sec: float = 30.0):
        self.url = url
        self.model = model
        self.timeout_sec = timeout_sec
        self.session = requests.Session()

    def healthcheck(self) -> None:
        base_url = self.url.rsplit("/api/", 1)[0]
        try:
            response = self.session.get(f"{base_url}/api/tags", timeout=3)
            response.raise_for_status()
        except requests.RequestException as exc:
            raise LLMUnavailableError(
                "Ollama에 연결할 수 없습니다. Ollama 실행 여부와 QUIZSENSE_OLLAMA_URL을 확인하세요."
            ) from exc

    def generate_package(self, context: str, question: str, max_tokens: int = 180) -> AnswerPackage:
        prompt = (
            "You are a concise real-time lecture assistant. Return only valid JSON with "
            'keys "question_ko", "answer_en", and "answer_ko". Keep each answer to at most two sentences. '
            f"\nLecture context:\n{context[-1200:]}\nQuestion:\n{question}"
        )
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "format": "json",
            "options": {"temperature": 0.2, "num_predict": max_tokens},
        }
        try:
            response = self.session.post(self.url, json=payload, timeout=self.timeout_sec)
            response.raise_for_status()
        except requests.RequestException as exc:
            raise LLMUnavailableError(f"Ollama 응답 생성 실패: {exc}") from exc
        raw = response.json().get("response", "")
        data = self._parse_json(raw)
        missing = {"question_ko", "answer_en", "answer_ko"} - data.keys()
        if missing:
            raise ValueError(f"LLM response is missing fields: {sorted(missing)}")
        return AnswerPackage(*(self._clean(data[key]) for key in ("question_ko", "answer_en", "answer_ko")))

    @staticmethod
    def _parse_json(text: str) -> dict[str, str]:
        cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip(), flags=re.I)
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", cleaned, flags=re.S)
            if not match:
                raise ValueError("LLM response was not valid JSON")
            return json.loads(match.group(0))

    @staticmethod
    def _clean(value: object) -> str:
        return re.sub(r"\s+", " ", str(value)).strip()
