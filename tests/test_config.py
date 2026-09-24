import pytest

from quizsense.config import AppConfig


def test_default_config_is_valid():
    AppConfig().validate()


def test_invalid_language_is_rejected():
    with pytest.raises(ValueError):
        AppConfig(language="fr").validate()


def test_block_size_is_derived():
    assert AppConfig(sample_rate=16_000, block_duration_sec=0.25).block_size == 4_000


def test_auto_language_maps_to_whisper_autodetection():
    assert AppConfig(language="auto").whisper_language is None
    assert AppConfig(language="ko").whisper_language == "ko"


def test_runtime_settings_are_loaded_from_environment(monkeypatch):
    monkeypatch.setenv("QUIZSENSE_LANGUAGE", "ko")
    monkeypatch.setenv("QUIZSENSE_SAMPLE_RATE", "48000")
    monkeypatch.setenv("QUIZSENSE_OLLAMA_TIMEOUT", "12.5")
    monkeypatch.setenv("QUIZSENSE_MAX_HISTORY", "25")

    config = AppConfig.from_env()

    assert config.whisper_language == "ko"
    assert config.sample_rate == 48_000
    assert config.ollama_timeout_sec == 12.5
    assert config.max_history_items == 25
