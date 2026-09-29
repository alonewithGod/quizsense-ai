import csv

from quizsense.evaluation import evaluate


def test_evaluation_reports_scenario_and_language_breakdowns(tmp_path):
    dataset = tmp_path / "scenario.csv"
    with dataset.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["id", "scenario", "language", "label", "text"])
        writer.writerow(["a-1", "alpha", "ko", "1", "왜 필요한가요?"])
        writer.writerow(["a-2", "alpha", "ko", "0", "필요한 기능입니다."])
        writer.writerow(["b-1", "beta", "en", "1", "What is a process?"])

    result = evaluate(dataset)

    assert result["samples"] == 3
    assert result["breakdown"]["scenario"]["alpha"]["samples"] == 2
    assert result["breakdown"]["scenario"]["beta"]["samples"] == 1
    assert result["breakdown"]["language"]["ko"]["samples"] == 2
    assert result["breakdown"]["language"]["en"]["samples"] == 1
