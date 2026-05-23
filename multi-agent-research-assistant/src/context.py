"""
ResearchContext — the single object passed between every agent.
No shared global state; all data lives here.
"""
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ResearchContext:
    # ── Input ─────────────────────────────────────────────────────
    topic: str
    depth: str = "standard"          # quick | standard | deep

    # ── Populated by ResearcherAgent ──────────────────────────────
    raw_findings: list[dict] = field(default_factory=list)
    # Each item: {"claim": str, "source": str}

    # ── Populated by FactCheckerAgent ─────────────────────────────
    verified_findings: list[dict] = field(default_factory=list)
    # Each item: {"claim": str, "source": str,
    #             "status": "verified"|"flagged"|"removed",
    #             "reason": str}

    # ── Populated by WriterAgent ──────────────────────────────────
    final_report: Optional[str] = None
    word_count: int = 0

    # ── Pipeline metadata ─────────────────────────────────────────
    elapsed: float = 0.0
    source_count: int = 0
    token_usage: dict = field(default_factory=dict)

    # ── Convenience properties ────────────────────────────────────
    @property
    def markdown(self) -> str:
        return self.final_report or ""

    @property
    def agent_count(self) -> int:
        return 3  # Researcher + FactChecker + Writer

    @property
    def verified_count(self) -> int:
        return sum(
            1 for f in self.verified_findings
            if f.get("status") == "verified"
        )

    def to_dict(self) -> dict:
        return {
            "topic": self.topic,
            "depth": self.depth,
            "word_count": self.word_count,
            "source_count": self.source_count,
            "elapsed_seconds": round(self.elapsed, 2),
            "verified_facts": self.verified_count,
            "verified_findings": self.verified_findings,
            "report": self.final_report,
            "token_usage": self.token_usage,
        }
