"""Base abstractions for the multi-agent consensus system.

Each specialized agent follows the same contract:

1. **gather()** deterministic evidence from a sales tool (always works, offline).
2. attempt an **LLM perspective** using its role prompt (real providers only).
3. fall back to a **deterministic narrative** when no LLM is available.

This keeps the system fully functional offline while genuinely using an LLM when
keys are configured — the behavior reviewers expect from a production agent.
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from app.agents.llm_text import complete_json
from app.agents.prompts import get_prompt_registry
from app.core import tracing


@dataclass
class AgentFinding:
    agent: str
    role: str
    insight: str
    confidence: float
    evidence: dict[str, Any] = field(default_factory=dict)
    source: str = "deterministic"  # "llm" or "deterministic"

    def to_dict(self) -> dict[str, Any]:
        return {
            "agent": self.agent,
            "role": self.role,
            "insight": self.insight,
            "confidence": round(self.confidence, 3),
            "source": self.source,
            "evidence": self.evidence,
        }


def _clamp_confidence(value: Any, default: float = 0.6) -> float:
    try:
        conf = float(value)
    except (TypeError, ValueError):
        return default
    return max(0.0, min(1.0, conf))


class Agent(ABC):
    """A specialized analyst that contributes one finding to the consensus."""

    name: str
    role: str
    prompt_name: str

    @abstractmethod
    def gather(self) -> dict[str, Any]:
        """Return deterministic evidence (tool output) for this agent."""

    @abstractmethod
    def fallback(self, evidence: dict[str, Any]) -> tuple[str, float]:
        """Return a deterministic (insight, confidence) when no LLM is available."""

    def analyze(self) -> AgentFinding:
        with tracing.span("agent", agent=self.name) as agent_span:
            evidence = self.gather()
            prompt = get_prompt_registry().get(self.prompt_name)
            filled = prompt.template.format(metrics=json.dumps(evidence, default=str))
            llm_result = complete_json(filled, "Return your JSON finding now.")

            if llm_result and llm_result.get("insight"):
                insight = str(llm_result["insight"]).strip()
                confidence = _clamp_confidence(llm_result.get("confidence"), 0.75)
                source = "llm"
            else:
                insight, confidence = self.fallback(evidence)
                source = "deterministic"

            agent_span.attributes.update({"source": source, "confidence": round(confidence, 3)})
            return AgentFinding(
                agent=self.name,
                role=self.role,
                insight=insight,
                confidence=confidence,
                evidence=evidence,
                source=source,
            )
