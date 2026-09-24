"""Runtime configuration loaded from environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass


def _env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    return default if value is None else int(value)


def _env_float(name: str, default: float) -> float:
    value = os.getenv(name)
    return default if value is None else float(value)


@dataclass(frozen=True)
class AppConfig:
    sample_rate: int = 16_000
    channels: int = 1
    block_duration_sec: float = 0.5
    rolling_context_sec: int = 24
    silence_rms_threshold: float = 0.01
    min_speech_blocks: int = 2
    min_silence_blocks_to_flush: int = 2
    whisper_model: str = "base"
    language: str = "auto"
    device: str = "cpu"
    compute_type: str = "int8"
    ollama_url: str = "http://localhost:11434/api/generate"
    ollama_model: str = "llama3.1:8b"
    question_cooldown_sec: float = 5.0
    duplicate_window_sec: float = 30.0
    max_history_items: int = 100
    ollama_timeout_sec: float = 30.0
    answer_max_tokens: int = 180
    log_dir: str = "artifacts/sessions"

    @property
    def block_size(self) -> int:
        return int(self.sample_rate * self.block_duration_sec)

    @property
    def whisper_language(self) -> str | None:
        return None if self.language == "auto" else self.language

    @classmethod
    def from_env(cls) -> "AppConfig":
        return cls(
            sample_rate=_env_int("QUIZSENSE_SAMPLE_RATE", cls.sample_rate),
            channels=_env_int("QUIZSENSE_CHANNELS", cls.channels),
            block_duration_sec=_env_float(
                "QUIZSENSE_BLOCK_DURATION", cls.block_duration_sec
            ),
            rolling_context_sec=_env_int(
                "QUIZSENSE_ROLLING_CONTEXT", cls.rolling_context_sec
            ),
            language=os.getenv("QUIZSENSE_LANGUAGE", cls.language),
            whisper_model=os.getenv("QUIZSENSE_WHISPER_MODEL", cls.whisper_model),
            device=os.getenv("QUIZSENSE_DEVICE", cls.device),
            compute_type=os.getenv("QUIZSENSE_COMPUTE_TYPE", cls.compute_type),
            ollama_url=os.getenv("QUIZSENSE_OLLAMA_URL", cls.ollama_url),
            ollama_model=os.getenv("QUIZSENSE_OLLAMA_MODEL", cls.ollama_model),
            silence_rms_threshold=_env_float(
                "QUIZSENSE_SILENCE_THRESHOLD", cls.silence_rms_threshold
            ),
            min_speech_blocks=_env_int(
                "QUIZSENSE_MIN_SPEECH_BLOCKS", cls.min_speech_blocks
            ),
            min_silence_blocks_to_flush=_env_int(
                "QUIZSENSE_MIN_SILENCE_BLOCKS", cls.min_silence_blocks_to_flush
            ),
            question_cooldown_sec=_env_float(
                "QUIZSENSE_QUESTION_COOLDOWN", cls.question_cooldown_sec
            ),
            duplicate_window_sec=_env_float(
                "QUIZSENSE_DUPLICATE_WINDOW", cls.duplicate_window_sec
            ),
            max_history_items=_env_int(
                "QUIZSENSE_MAX_HISTORY", cls.max_history_items
            ),
            ollama_timeout_sec=_env_float(
                "QUIZSENSE_OLLAMA_TIMEOUT", cls.ollama_timeout_sec
            ),
            answer_max_tokens=_env_int(
                "QUIZSENSE_ANSWER_MAX_TOKENS", cls.answer_max_tokens
            ),
            log_dir=os.getenv("QUIZSENSE_LOG_DIR", cls.log_dir),
        )

    def validate(self) -> None:
        if self.sample_rate <= 0 or self.block_duration_sec <= 0:
            raise ValueError("sample rate and block duration must be positive")
        if self.channels <= 0:
            raise ValueError("channels must be positive")
        if self.language not in {"auto", "en", "ko"}:
            raise ValueError("language must be one of: auto, en, ko")
        if not 0 < self.silence_rms_threshold < 1:
            raise ValueError("silence RMS threshold must be between 0 and 1")
        if self.question_cooldown_sec < 0:
            raise ValueError("question cooldown cannot be negative")
        if self.min_speech_blocks <= 0 or self.min_silence_blocks_to_flush <= 0:
            raise ValueError("speech and silence block counts must be positive")
        if self.duplicate_window_sec < 0:
            raise ValueError("duplicate window cannot be negative")
        if self.max_history_items <= 0 or self.answer_max_tokens <= 0:
            raise ValueError("history size and answer token limit must be positive")
        if self.ollama_timeout_sec <= 0:
            raise ValueError("Ollama timeout must be positive")
