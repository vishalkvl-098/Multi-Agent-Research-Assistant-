"""
Tests for WriterAgent — focuses on context population and edge cases.
"""
import pytest
from src.agents.writer import WriterAgent
from src.context import ResearchContext

VERIFIED_FINDINGS = [
    {"claim": "AI market valued at $200B in 2024.", "source": "https://gartner.com", "status": "verified", "reason": ""},
    {"claim": "LLMs showed 40% improvement in coding benchmarks.", "source": "https://openai.com", "status": "verified", "reason": ""},
    {"claim": "AI adoption in healthcare reached 60% of hospitals.", "source": "https://hhs.gov", "status": "flagged", "reason": "Estimate varies by region"},
]


@pytest.fixture
def agent():
    return WriterAgent(model="claude-sonnet-4-6")


def test_run_no_usable_facts(agent):
    """Writer should produce a fallback message if no usable facts."""
    ctx = ResearchContext(topic="Test topic")
    ctx.verified_findings = [
        {"claim": "Bad claim", "source": "x", "status": "removed", "reason": "wrong"}
    ]
    ctx = agent.run(ctx)
    assert ctx.final_report is not None
    assert "No verified findings" in ctx.final_report


def test_word_count_set(agent, monkeypatch):
    """word_count should be set after run."""
    monkeypatch.setattr(
        agent, "call",
        lambda **kw: "# Report\n\n" + " ".join(["word"] * 100)
    )
    ctx = ResearchContext(topic="AI trends 2024")
    ctx.verified_findings = VERIFIED_FINDINGS
    ctx = agent.run(ctx)
    assert ctx.word_count > 0


def test_final_report_is_string(agent, monkeypatch):
    monkeypatch.setattr(agent, "call", lambda **kw: "# My Report\n\nSome content here.")
    ctx = ResearchContext(topic="Topic")
    ctx.verified_findings = VERIFIED_FINDINGS
    ctx = agent.run(ctx)
    assert isinstance(ctx.final_report, str)
    assert len(ctx.final_report) > 0


def test_flagged_facts_included(agent, monkeypatch):
    """Flagged findings should still be passed to the writer."""
    called_with = {}

    def fake_call(**kw):
        called_with["user"] = kw.get("user", "")
        return "# Report\n\nContent."

    monkeypatch.setattr(agent, "call", fake_call)
    ctx = ResearchContext(topic="Topic")
    ctx.verified_findings = VERIFIED_FINDINGS
    agent.run(ctx)
    # The flagged finding's claim should appear in the prompt
    assert "AI adoption in healthcare" in called_with.get("user", "")
