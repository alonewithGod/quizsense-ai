"""Runtime dependency checks for a reproducible live demonstration."""

from __future__ import annotations

import argparse
import importlib.util
import json
from dataclasses import asdict, dataclass
from typing import Callable
from urllib.parse import urlsplit, urlunsplit

import requests

from .config import AppConfig


@dataclass(frozen=True)
class CheckResult:
    name: str
    ok: bool
    detail: str


def _module_available(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def _input_device_detail() -> str:
    import sounddevice as sd

    device = sd.query_devices(kind="input")
    return str(device.get("name", "input device detected"))


def _ollama_models(url: str, timeout_sec: float) -> list[str]:
    parsed = urlsplit(url)
    tags_url = urlunsplit((parsed.scheme, parsed.netloc, "/api/tags", "", ""))
    response = requests.get(tags_url, timeout=timeout_sec)
    response.raise_for_status()
    payload = response.json()
    return [str(model.get("name", "")) for model in payload.get("models", [])]


def run_preflight(
    config: AppConfig,
    module_available: Callable[[str], bool] = _module_available,
    input_device_detail: Callable[[], str] = _input_device_detail,
    ollama_models: Callable[[str, float], list[str]] = _ollama_models,
) -> list[CheckResult]:
    results: list[CheckResult] = []

    for module_name in ("sounddevice", "faster_whisper"):
        available = module_available(module_name)
        results.append(
            CheckResult(
                name=f"module:{module_name}",
                ok=available,
                detail="installed" if available else "not installed",
            )
        )

    if module_available("sounddevice"):
        try:
            results.append(CheckResult("input_device", True, input_device_detail()))
        except Exception as exc:
            results.append(CheckResult("input_device", False, str(exc)))
    else:
        results.append(CheckResult("input_device", False, "sounddevice is not installed"))

    try:
        models = ollama_models(config.ollama_url, config.ollama_timeout_sec)
        model_ready = config.ollama_model in models
        detail = (
            f"{config.ollama_model} is available"
            if model_ready
            else f"{config.ollama_model} is missing; installed: {', '.join(models) or 'none'}"
        )
        results.append(CheckResult("ollama_model", model_ready, detail))
    except Exception as exc:
        results.append(CheckResult("ollama_model", False, str(exc)))

    return results


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check QuizSense live-run dependencies.")
    parser.add_argument("--json", action="store_true", help="print machine-readable JSON")
    args = parser.parse_args(argv)

    try:
        config = AppConfig.from_env()
        config.validate()
        results = run_preflight(config)
    except Exception as exc:
        results = [CheckResult("configuration", False, str(exc))]

    if args.json:
        print(json.dumps([asdict(result) for result in results], ensure_ascii=False, indent=2))
    else:
        for result in results:
            mark = "PASS" if result.ok else "FAIL"
            print(f"[{mark}] {result.name}: {result.detail}")

    return 0 if all(result.ok for result in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
