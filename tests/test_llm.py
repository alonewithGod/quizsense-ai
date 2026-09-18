import pytest

from quizsense.llm import OllamaClient


def test_parse_json_accepts_markdown_fence():
    parsed = OllamaClient._parse_json('```json\n{"answer_en":"A"}\n```')
    assert parsed["answer_en"] == "A"


def test_parse_json_rejects_non_json():
    with pytest.raises(ValueError):
        OllamaClient._parse_json("not structured output")
