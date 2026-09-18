import pytest

from quizsense.config import AppConfig


def test_default_config_is_valid():
    AppConfig().validate()


def test_invalid_language_is_rejected():
    with pytest.raises(ValueError):
        AppConfig(language="fr").validate()


def test_block_size_is_derived():
    assert AppConfig(sample_rate=16_000, block_duration_sec=0.25).block_size == 4_000
