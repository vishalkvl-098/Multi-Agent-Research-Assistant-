"""
Tests for FactCheckerAgent — focuses on JSON parsing and fallback logic.
"""
import json
import pytest
from src.agents.fact_checker import FactCheckerAgent
from src.context import ResearchContext

SAMPLE_FINDINGS = [
    {"claim": "Global EV sales reached 14 million in 2023.", "source": "https://iea.org"},
    {"claim": "EVs will fully replace ICE by 2025.", "source": "unknown"},
    {"claim": "Battery costs dropped significantly.", "source": "https://bnef.com"},
]


@pytest.fixture
def agent():
    return FactCheckerAgent(model="claude-sonnet-4-6")


def test_parse_results_valid_json(agent):
    results = [
        {"claim": "Fact A", "source": "https://a.com", "status": "verified", "reason": ""},
        {"claim": "Fact B", "source": "unknown", "status": "removed", "reason": "Speculative"},
    ]
    text = json.dumps(results)
    parsed = agent._parse_results(text, SAMPLE_FINDINGS)
    assert len(parsed) == 2
    assert parsed[0]["status"] == "verified"
    assert parsed[1]["status"] == "removed"


def test_parse_results_with_json_fences(agent):
    results = [{"claim": "X", "source": "y", "status": "verified", "reason": ""}]
    text = f"```json\n{json.dumps(results)}\n```"
    parsed = agent._parse_results(text, SAMPLE_FINDINGS)
    assert len(parsed) == 1


def test_parse_results_invalid_json_falls_back(agent):
    parsed = agent._parse_results("not json at all {{{}}", SAMPLE_FINDINGS)
    # Should fall back to returning all originals as verified
    assert len(parsed) == len(SAMPLE_FINDINGS)
    assert all(f["status"] == "verified" for f in parsed)


def test_parse_results_invalid_status_defaults(agent):
    results = [{"claim": "X", "source": "y", "status": "maybe", "reason": ""}]
    text = json.dumps(results)
    parsed = agent._parse_results(text, [])
    assert parsed[0]["status"] == "verified"


def test_fallback(agent):
    fb = agent._fallback(SAMPLE_FINDINGS)
    assert len(fb) == len(SAMPLE_FINDINGS)
    assert all(f["status"] == "verified" for f in fb)


def test_run_empty_findings(agent, monkeypatch):
    ctx = ResearchContext(topic="Test", depth="standard")
    ctx = agent.run(ctx)
    assert ctx.verified_findings == []
