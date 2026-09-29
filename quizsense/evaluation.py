"""Reproducible question-detection evaluation CLI."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from .question_detection import QuestionDetector


def _metrics(rows: list[dict[str, object]]) -> dict[str, object]:
    tp = sum(bool(r["expected"]) and bool(r["predicted"]) for r in rows)
    tn = sum(not bool(r["expected"]) and not bool(r["predicted"]) for r in rows)
    fp = sum(not bool(r["expected"]) and bool(r["predicted"]) for r in rows)
    fn = sum(bool(r["expected"]) and not bool(r["predicted"]) for r in rows)
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {
        "samples": len(rows),
        "confusion_matrix": {"tp": tp, "tn": tn, "fp": fp, "fn": fn},
        "accuracy": round((tp + tn) / len(rows), 4) if rows else 0.0,
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
    }


def evaluate(dataset_path: str | Path) -> dict[str, object]:
    detector = QuestionDetector(cooldown_sec=0)
    rows: list[dict[str, object]] = []
    with Path(dataset_path).open(encoding="utf-8-sig", newline="") as stream:
        for row in csv.DictReader(stream):
            expected = row["label"].strip() == "1"
            decision = detector.classify(row["text"])
            rows.append(
                {
                    **row,
                    "expected": expected,
                    "predicted": decision.is_question,
                    "score": decision.score,
                    "reasons": list(decision.reasons),
                }
            )
    breakdown: dict[str, dict[str, object]] = {}
    for field in ("scenario", "language"):
        values = sorted({str(row[field]) for row in rows if row.get(field)})
        if values:
            breakdown[field] = {
                value: _metrics([row for row in rows if row.get(field) == value])
                for value in values
            }
    return {
        "dataset": str(dataset_path),
        **_metrics(rows),
        "breakdown": breakdown,
        "errors": [r for r in rows if r["expected"] != r["predicted"]],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("dataset")
    parser.add_argument("--output")
    args = parser.parse_args()
    result = evaluate(args.dataset)
    rendered = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text(rendered + "\n", encoding="utf-8")
    print(rendered)


if __name__ == "__main__":
    main()
