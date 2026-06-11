"""Tests for the multi-agent consensus system."""

from app.agents.base import AgentFinding
from app.agents.consensus import (
    AgentOrchestrator,
    ConsensusWorkspace,
    ForecastingSpecialistAgent,
    ReconcilerAgent,
    RiskAssessorAgent,
    TrendAnalystAgent,
    run_consensus_analysis,
)
from app.main import app
from fastapi.testclient import TestClient


class TestSpecializedAgents:
    def test_each_agent_produces_a_finding(self) -> None:
        for agent_cls in (TrendAnalystAgent, RiskAssessorAgent, ForecastingSpecialistAgent):
            finding = agent_cls().analyze()
            assert isinstance(finding, AgentFinding)
            assert finding.insight
            assert 0.0 <= finding.confidence <= 1.0
            assert finding.evidence  # tool output attached
            assert finding.source in {"llm", "deterministic"}

    def test_agents_have_distinct_roles(self) -> None:
        roles = {
            TrendAnalystAgent().role,
            RiskAssessorAgent().role,
            ForecastingSpecialistAgent().role,
        }
        assert roles == {"trend", "risk", "forecast"}


class TestReconciler:
    def test_reconcile_produces_verdict(self) -> None:
        workspace = ConsensusWorkspace()
        workspace.publish(TrendAnalystAgent().analyze())
        workspace.publish(RiskAssessorAgent().analyze())
        workspace.publish(ForecastingSpecialistAgent().analyze())

        verdict = ReconcilerAgent().reconcile(workspace)
        assert verdict.insight
        assert 0.0 <= verdict.confidence <= 1.0
        assert isinstance(verdict.conflicts, list)

    def test_detects_optimism_vs_risk_conflict(self) -> None:
        workspace = ConsensusWorkspace()
        workspace.publish(
            AgentFinding(
                "Forecasting Specialist",
                "forecast",
                "up",
                0.8,
                evidence={"trend_direction": "increasing"},
            )
        )
        workspace.publish(
            AgentFinding("Risk Assessor", "risk", "risky", 0.8, evidence={"anomaly_count": 3})
        )
        conflicts = ReconcilerAgent()._detect_conflicts(workspace)
        assert any("fragile" in c or "anomalies" in c for c in conflicts)


class TestOrchestrator:
    def test_full_pipeline_structure(self) -> None:
        result = AgentOrchestrator().run("how are sales trending")
        assert result["agent_count"] == 3
        assert len(result["findings"]) == 3
        assert result["reconciled"]["insight"]

    def test_run_consensus_analysis_attaches_trace(self) -> None:
        result = run_consensus_analysis("give me the outlook")
        assert result["trace_id"]
        from app.core.tracing import get_trace_store

        trace = get_trace_store().get(result["trace_id"])
        assert trace is not None
        span_names = {s.name for s in trace.spans}
        assert "consensus" in span_names


class TestConsensusEndpoint:
    def setup_method(self) -> None:
        self.client = TestClient(app)

    def test_endpoint_returns_full_consensus(self) -> None:
        resp = self.client.post("/analyze/consensus", json={"query": "what's the outlook?"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["agent_count"] == 3
        assert len(body["findings"]) == 3
        assert body["reconciled"]["insight"]
        assert body["trace_id"]
