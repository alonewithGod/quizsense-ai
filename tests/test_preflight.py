import json

from quizsense.config import AppConfig
from quizsense.preflight import CheckResult, build_report, main, run_preflight


def test_preflight_passes_when_dependencies_device_and_model_are_ready():
    results = run_preflight(
        AppConfig(ollama_model="llama3.1:8b"),
        module_available=lambda name: name in {"sounddevice", "faster_whisper"},
        input_device_detail=lambda: "Test Microphone",
        ollama_models=lambda url, timeout: ["llama3.1:8b"],
    )

    assert all(result.ok for result in results)
    assert results[-1].detail == "llama3.1:8b is available"


def test_preflight_reports_missing_runtime_requirements():
    results = run_preflight(
        AppConfig(ollama_model="llama3.1:8b"),
        module_available=lambda name: name == "faster_whisper",
        input_device_detail=lambda: "unused",
        ollama_models=lambda url, timeout: ["qwen2.5:3b"],
    )
    by_name = {result.name: result for result in results}

    assert not by_name["module:sounddevice"].ok
    assert by_name["input_device"].detail == "sounddevice is not installed"
    assert not by_name["ollama_model"].ok
    assert "llama3.1:8b is missing" in by_name["ollama_model"].detail


def test_cli_returns_failure_for_invalid_environment(monkeypatch, capsys):
    monkeypatch.setenv("QUIZSENSE_LANGUAGE", "unsupported")

    assert main(["--json"]) == 1
    assert '"name": "configuration"' in capsys.readouterr().out


def test_report_records_runtime_and_readiness():
    report = build_report(
        AppConfig(language="ko", whisper_model="small", ollama_model="test:latest"),
        [CheckResult("input_device", True, "Test Microphone")],
    )

    assert report["ready"] is True
    assert report["runtime"]["language"] == "ko"
    assert report["runtime"]["whisper_model"] == "small"
    assert report["runtime"]["ollama_model"] == "test:latest"
    assert report["checks"][0]["detail"] == "Test Microphone"
    assert str(report["generated_at_utc"]).endswith("+00:00")


def test_cli_saves_failure_report_for_invalid_environment(monkeypatch, tmp_path):
    monkeypatch.setenv("QUIZSENSE_LANGUAGE", "unsupported")
    output = tmp_path / "reports" / "preflight.json"

    assert main(["--output", str(output)]) == 1

    report = json.loads(output.read_text(encoding="utf-8"))
    assert report["ready"] is False
    assert report["runtime"]["language"] == "unsupported"
    assert report["checks"][0]["name"] == "configuration"
