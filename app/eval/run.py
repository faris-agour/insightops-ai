"""Eval runner: scores the rule-based intent classifier against the golden set.

Run with::

    python -m app.eval.run            # human-readable report
    python -m app.eval.run --json     # machine-readable JSON
    python -m app.eval.run --threshold 0.9

Exits non-zero when accuracy falls below the threshold, so CI can gate on it.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from dataclasses import dataclass, field

from app.agents.simple_agent import classify_task
from app.eval.dataset import GOLDEN_CASES


@dataclass
class EvalReport:
    total: int
    correct: int
    failures: list[dict[str, str]] = field(default_factory=list)
    per_intent: dict[str, dict[str, int]] = field(default_factory=dict)

    @property
    def accuracy(self) -> float:
        return round(self.correct / self.total, 4) if self.total else 0.0

    def to_dict(self) -> dict[str, object]:
        return {
            "total": self.total,
            "correct": self.correct,
            "accuracy": self.accuracy,
            "failures": self.failures,
            "per_intent": self.per_intent,
        }


def evaluate(classifier=classify_task) -> EvalReport:
    correct = 0
    failures: list[dict[str, str]] = []
    per_intent: dict[str, dict[str, int]] = defaultdict(lambda: {"total": 0, "correct": 0})

    for query, expected in GOLDEN_CASES:
        predicted = classifier(query)
        per_intent[expected]["total"] += 1
        if predicted == expected:
            correct += 1
            per_intent[expected]["correct"] += 1
        else:
            failures.append({"query": query, "expected": expected, "predicted": predicted})

    return EvalReport(
        total=len(GOLDEN_CASES),
        correct=correct,
        failures=failures,
        per_intent=dict(per_intent),
    )


def _render_human(report: EvalReport) -> str:
    lines = [
        "=" * 56,
        " InsightOps AI - Intent Classification Eval",
        "=" * 56,
        f" Accuracy : {report.accuracy:.1%}  ({report.correct}/{report.total})",
        "-" * 56,
        " Per-intent recall:",
    ]
    for intent, stats in sorted(report.per_intent.items()):
        rate = stats["correct"] / stats["total"] if stats["total"] else 0.0
        lines.append(f"   {intent:<20} {stats['correct']}/{stats['total']}  ({rate:.0%})")
    if report.failures:
        lines.append("-" * 56)
        lines.append(" Failures:")
        for f in report.failures:
            lines.append(f"   '{f['query']}' -> got '{f['predicted']}', want '{f['expected']}'")
    lines.append("=" * 56)
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the intent classification eval.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of a table.")
    parser.add_argument("--threshold", type=float, default=0.8, help="Min accuracy to pass.")
    args = parser.parse_args(argv)

    report = evaluate()
    if args.json:
        print(json.dumps(report.to_dict(), indent=2))
    else:
        print(_render_human(report))

    if report.accuracy < args.threshold:
        print(f"\nFAIL: accuracy {report.accuracy:.1%} < threshold {args.threshold:.1%}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
