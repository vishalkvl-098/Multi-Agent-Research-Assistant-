"""
Tests for ResearcherAgent — focuses on parsing logic
(no API calls required).
"""
import pytest
from src.agents.researcher import ResearcherAgent
from src.context import ResearchContext


@pytest.fixture
def agent():
    return ResearcherAgent(model="claude-sonnet-4-6")


def test_parse_findings_basic(agent):
    text = (
        "FINDING: Global EV sales hit 14 million units in 2023.\n"
        "SOURCE: https://iea.org/ev-outlook\n"
        "FINDING: Battery costs fell 90% between 2010 and 2023.\n"
        "SOURCE: https://bnef.com/batteries\n"
    )
    results = agent._parse_findings(text)
    assert len(results) == 2
    assert results[0]["claim"] == "Global EV sales hit 14 million units in 2023."
    assert results[0]["source"] == "https://iea.org/ev-outlook"
    assert results[1]["claim"] == "Battery costs fell 90% between 2010 and 2023."


def test_parse_findings_case_insensitive(agent):
    text = (
        "finding: Some fact here.\n"
        "source: https://example.com\n"
    )
    results = agent._parse_findings(text)
    assert len(results) == 1


def test_parse_findings_deduplication(agent):
    text = (
        "FINDING: AI market worth $200 billion in 2024.\n"
        "SOURCE: https://example.com\n"
        "FINDING: AI market worth $200 billion in 2024.\n"
        "SOURCE: https://other.com\n"
    )
    results = agent._parse_findings(text)
    assert len(results) == 1


def test_parse_findings_missing_source(agent):
    text = "FINDING: Some interesting fact without a source.\n"
    results = agent._parse_findings(text)
    assert len(results) == 1
    assert results[0]["source"] == "unknown"


def test_parse_findings_empty(agent):
    results = agent._parse_findings("")
    assert results == []


def test_context_populated(agent, monkeypatch):
    """Researcher should populate raw_findings on context."""
    fake_output = (
        "FINDING: Fact one.\nSOURCE: https://a.com\n"
        "FINDING: Fact two.\nSOURCE: https://b.com\n"
    )
    monkeypatch.setattr(
        agent, "call",
        lambda system, user, tools=None, max_tokens=2048: fake_output
    )
    ctx = ResearchContext(topic="Test topic")
    ctx = agent.run(ctx)
    assert len(ctx.raw_findings) == 2
    assert ctx.raw_findings[0]["claim"] == "Fact one."
