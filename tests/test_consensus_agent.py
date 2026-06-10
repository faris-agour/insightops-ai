"""Backward-compatibility tests for the legacy run_consensus shim."""

from app.agents.consensus_agent import run_consensus


def test_run_consensus_returns_reconciled_string() -> None:
    result = run_consensus("How are sales doing this year?")
    assert isinstance(result, str)
    assert "Reconciled Insight" in result
    assert len(result) > 30
