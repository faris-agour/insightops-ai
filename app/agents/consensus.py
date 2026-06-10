"""Multi-agent collaborative consensus.

Three specialized agents independently analyze the same sales data from different
angles (trend, risk, forecast), publish their findings to a shared workspace, and a
Reconciler agent synthesizes them into a single executive verdict — explicitly
surfacing tension between optimism and risk.

Flow::

    AgentOrchestrator
        ├── TrendAnalystAgent ───┐
        ├── RiskAssessorAgent ───┤──► ConsensusWorkspace ──► ReconcilerAgent ──► verdict
        └── ForecastingSpecialist ┘

Works fully offline (deterministic narratives) and upgrades to real LLM reasoning
when provider keys are configured.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from app.agents.base import Agent, AgentFinding, _clamp_confidence
from app.agents.llm_text import complete_json
from app.agents.prompts import get_prompt_registry
from app.analysis.advanced_analytics import analyze_trend, detect_anomalies, forecast_revenue
from app.core import tracing
from app.core.logging_config import get_logger

logger = get_logger(__name__)


# --- Specialized agents ------------------------------------------------------

class TrendAnalystAgent(Agent):
    name = "Trend Analyst"
    role = "trend"
    prompt_name = "trend_analyst"

    def gather(self) -> dict[str, Any]:
        return analyze_trend()

    def fallback(self, evidence: dict[str, Any]) -> tuple[str, float]:
        trend = str(evidence.get("trend", "stable"))
        change = float(evidence.get("change_percent", 0.0) or 0.0)
        if trend == "increasing":
            return (
                f"Momentum is positive: the smoothed series climbed {change:+.1f}% across the window.",
                0.85,
            )
        if trend == "decreasing":
            return (
                f"Momentum is weakening: the smoothed series fell {change:+.1f}% across the window.",
                0.85,
            )
        return (
            f"Momentum is flat ({change:+.1f}% smoothed change) — no decisive directional signal.",
            0.6,
        )


class RiskAssessorAgent(Agent):
    name = "Risk Assessor"
    role = "risk"
    prompt_name = "risk_assessor"

    def gather(self) -> dict[str, Any]:
        return detect_anomalies()

    def fallback(self, evidence: dict[str, Any]) -> tuple[str, float]:
        count = int(evidence.get("anomaly_count", 0) or 0)
        if count == 0:
            return ("No revenue anomalies detected; operations look stable.", 0.7)
        anomalies = evidence.get("anomalies", []) or []
        drops = sum(1 for a in anomalies if isinstance(a, dict) and a.get("direction") == "drop")
        return (
            f"{count} anomalies detected ({drops} downside) — volatility introduces planning risk.",
            0.8,
        )


class ForecastingSpecialistAgent(Agent):
    name = "Forecasting Specialist"
    role = "forecast"
    prompt_name = "forecasting_specialist"

    def gather(self) -> dict[str, Any]:
        return forecast_revenue()

    def fallback(self, evidence: dict[str, Any]) -> tuple[str, float]:
        direction = str(evidence.get("trend_direction", "flat"))
        slope = float(evidence.get("daily_growth_estimate", 0.0) or 0.0)
        return (
            f"Near-term forecast is {direction} (~${slope:,.0f}/day drift via linear regression).",
            0.7,
        )


# --- Workspace ---------------------------------------------------------------

@dataclass
class ConsensusWorkspace:
    """Shared blackboard collecting findings from all specialized agents."""

    findings: list[AgentFinding] = field(default_factory=list)

    def publish(self, finding: AgentFinding) -> None:
        self.findings.append(finding)

    def serialize(self) -> list[dict[str, Any]]:
        return [f.to_dict() for f in self.findings]


# --- Reconciler --------------------------------------------------------------

@dataclass
class ReconciledVerdict:
    insight: str
    confidence: float
    conflicts: list[str]
    source: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "insight": self.insight,
            "confidence": round(self.confidence, 3),
            "conflicts": self.conflicts,
            "source": self.source,
        }


class ReconcilerAgent:
    name = "Reconciler"

    def _detect_conflicts(self, workspace: ConsensusWorkspace) -> list[str]:
        by_role = {f.role: f for f in workspace.findings}
        conflicts: list[str] = []
        forecast = by_role.get("forecast")
        risk = by_role.get("risk")
        trend = by_role.get("trend")

        forecast_up = forecast and "increasing" in forecast.evidence.get("trend_direction", "")
        risk_flagged = risk and int(risk.evidence.get("anomaly_count", 0) or 0) > 0
        if forecast_up and risk_flagged:
            conflicts.append(
                "Optimistic forecast coexists with detected anomalies — growth may be fragile."
            )
        if trend and forecast:
            t_dir = trend.evidence.get("trend", "stable")
            f_dir = forecast.evidence.get("trend_direction", "flat")
            if t_dir == "increasing" and f_dir == "decreasing":
                conflicts.append("Historical momentum is up but the forward forecast points down.")
            elif t_dir == "decreasing" and f_dir == "increasing":
                conflicts.append("Historical momentum is down but the forward forecast points up.")
        return conflicts

    def reconcile(self, workspace: ConsensusWorkspace) -> ReconciledVerdict:
        with tracing.span("reconcile", agents=len(workspace.findings)) as span:
            conflicts = self._detect_conflicts(workspace)
            prompt = get_prompt_registry().get("reconciler")
            filled = prompt.template.format(findings=json.dumps(workspace.serialize(), default=str))
            llm_result = complete_json(filled, "Return your reconciled JSON now.")

            if llm_result and llm_result.get("insight"):
                verdict = ReconciledVerdict(
                    insight=str(llm_result["insight"]).strip(),
                    confidence=_clamp_confidence(llm_result.get("confidence"), 0.75),
                    conflicts=conflicts,
                    source="llm",
                )
            else:
                verdict = self._fallback(workspace, conflicts)

            span.attributes.update({"source": verdict.source, "conflicts": len(conflicts)})
            return verdict

    def _fallback(
        self, workspace: ConsensusWorkspace, conflicts: list[str]
    ) -> ReconciledVerdict:
        parts = [f"{f.agent}: {f.insight}" for f in workspace.findings]
        avg_conf = (
            sum(f.confidence for f in workspace.findings) / len(workspace.findings)
            if workspace.findings
            else 0.0
        )
        tension = (
            " Caution: " + " ".join(conflicts)
            if conflicts
            else " The signals are mutually consistent."
        )
        recommendation = (
            " Recommendation: act on the forecast while hedging against the flagged risks."
            if conflicts
            else " Recommendation: proceed with the prevailing trend and keep monitoring."
        )
        insight = (
            "Integrated view -> " + " | ".join(parts) + "." + tension + recommendation
        )
        # Conflicts reduce overall confidence in a single cohesive call.
        confidence = max(0.4, avg_conf - 0.1 * len(conflicts))
        return ReconciledVerdict(
            insight=insight, confidence=confidence, conflicts=conflicts, source="deterministic"
        )


# --- Orchestrator ------------------------------------------------------------

class AgentOrchestrator:
    def __init__(self) -> None:
        self.agents: list[Agent] = [
            TrendAnalystAgent(),
            RiskAssessorAgent(),
            ForecastingSpecialistAgent(),
        ]
        self.reconciler = ReconcilerAgent()

    def run(self, query: str) -> dict[str, Any]:
        workspace = ConsensusWorkspace()
        for agent in self.agents:
            try:
                workspace.publish(agent.analyze())
            except Exception as exc:  # noqa: BLE001 - one agent must not sink the panel
                logger.exception("Agent %s failed: %s", agent.name, exc)

        verdict = self.reconciler.reconcile(workspace)
        return {
            "query": query,
            "agent_count": len(workspace.findings),
            "findings": workspace.serialize(),
            "reconciled": verdict.to_dict(),
        }


_orchestrator: AgentOrchestrator | None = None


def get_orchestrator() -> AgentOrchestrator:
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = AgentOrchestrator()
    return _orchestrator


def run_consensus_analysis(query: str) -> dict[str, Any]:
    """Run the full multi-agent consensus pipeline within a trace."""
    trace = tracing.start_trace(query)
    with tracing.span("consensus"):
        result = get_orchestrator().run(query)
    result["trace_id"] = trace.trace_id
    tracing.finish_trace(
        trace,
        mode="consensus",
        agents=result["agent_count"],
        reconciled_confidence=result["reconciled"]["confidence"],
    )
    return result
