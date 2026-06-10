"""Backward-compatible entry point for the consensus system.

The real implementation now lives in :mod:`app.agents.consensus`. This thin shim
preserves the original ``run_consensus(query) -> str`` signature used by early
prototypes and tests, returning the reconciled insight as a string.
"""

from __future__ import annotations

from app.agents.consensus import run_consensus_analysis


def run_consensus(query: str) -> str:
    result = run_consensus_analysis(query)
    insight = result["reconciled"]["insight"]
    return f"Reconciled Insight: {insight}"
