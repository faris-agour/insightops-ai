"""Tests for the offline eval harness."""

from app.eval.run import evaluate, main


def test_golden_set_accuracy_is_high() -> None:
    report = evaluate()
    assert report.total >= 20
    assert report.accuracy >= 0.8


def test_report_serialization() -> None:
    report = evaluate()
    data = report.to_dict()
    assert set(data) >= {"total", "correct", "accuracy", "failures", "per_intent"}


def test_main_passes_with_low_threshold() -> None:
    assert main(["--json", "--threshold", "0.5"]) == 0


def test_main_fails_with_impossible_threshold() -> None:
    assert main(["--threshold", "1.01"]) == 1
