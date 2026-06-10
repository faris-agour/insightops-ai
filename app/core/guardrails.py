"""Input/output guardrails for the LLM layer.

Two responsibilities:

1. **Prompt-injection screening** — flag queries that try to override the system
   instructions. The router treats user input as data, but flagging lets us
   observe and rate-limit abuse.
2. **PII redaction** — scrub emails, phone numbers, and card-like sequences from
   anything that reaches the logs, so observability never leaks sensitive data.

Heuristic by design (no model call) so it is fast, deterministic, and testable.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

_INJECTION_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("override_instructions", re.compile(r"\b(ignore|disregard|forget)\b.{0,20}\b(previous|above|prior|system)\b", re.I)),
    ("reveal_system_prompt", re.compile(r"\b(system prompt|your instructions|your rules|reveal).{0,20}\b(prompt|instructions|rules)\b", re.I)),
    ("role_hijack", re.compile(r"\byou are now\b|\bact as\b|\bpretend to be\b", re.I)),
    ("instruction_injection", re.compile(r"\bnew instructions?\b|\boverride\b|\bjailbreak\b", re.I)),
)

_EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
_PHONE_RE = re.compile(r"(?<!\d)(?:\+?\d{1,3}[\s-]?)?(?:\(?\d{3}\)?[\s-]?)\d{3}[\s-]?\d{4}(?!\d)")
_CARD_RE = re.compile(r"(?<!\d)(?:\d[ -]?){13,16}(?!\d)")


@dataclass
class GuardrailResult:
    flagged: bool
    reasons: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return {"flagged": self.flagged, "reasons": self.reasons}


def scan_input(text: str) -> GuardrailResult:
    """Screen a user query for prompt-injection signals."""
    reasons = [name for name, pattern in _INJECTION_PATTERNS if pattern.search(text)]
    return GuardrailResult(flagged=bool(reasons), reasons=reasons)


def redact_pii(text: str) -> str:
    """Return ``text`` with emails, phone numbers, and card-like digits masked."""
    if not text:
        return text
    redacted = _EMAIL_RE.sub("[REDACTED_EMAIL]", text)
    redacted = _CARD_RE.sub("[REDACTED_CARD]", redacted)
    redacted = _PHONE_RE.sub("[REDACTED_PHONE]", redacted)
    return redacted
