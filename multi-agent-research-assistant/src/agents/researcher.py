"""
ResearcherAgent — searches the web and gathers raw findings.

Responsibilities:
  - Break the topic into targeted sub-queries
  - Use Claude's web_search tool to fetch live results
  - Return a structured list of (claim, source) pairs
"""
from src.agents.base_agent import BaseAgent
from src.context import ResearchContext

# ── Depth → search breadth mapping ───────────────────────────────
DEPTH_CONFIG = {
    "quick":    {"max_queries": 2, "max_tokens": 2000},
    "standard": {"max_queries": 4, "max_tokens": 3000},
    "deep":     {"max_queries": 6, "max_tokens": 4000},
}

# ── System prompt ─────────────────────────────────────────────────
RESEARCHER_SYSTEM = """
You are an expert research agent. Your job is to gather accurate,
current information on the given topic using web search.

PROCESS:
1. Break the topic into specific, targeted sub-queries
2. Search each sub-query using the web_search tool
3. Extract the most relevant, concrete facts from results

OUTPUT FORMAT — respond with ONLY this format, one per line:
FINDING: <a single, concrete factual statement>
SOURCE: <URL or source name>

Rules:
- Each FINDING must be a single, self-contained fact
- Pair every FINDING immediately with its SOURCE
- Focus on recent data (last 1-2 years when relevant)
- Include numbers, statistics, and specific details when found
- Do NOT include opinions, predictions, or vague statements
- Aim for {num_findings} distinct findings
"""

WEB_SEARCH_TOOL = {
    "type": "web_search_20250305",
    "name": "web_search",
}


class ResearcherAgent(BaseAgent):
    def __init__(self, model: str, verbose: bool = False):
        super().__init__(model, "Researcher", verbose)

    def run(self, context: ResearchContext) -> ResearchContext:
        cfg = DEPTH_CONFIG.get(context.depth, DEPTH_CONFIG["standard"])
        num_findings = cfg["max_queries"] * 3

        self.logger.info(
            f'Researching: [bold]"{context.topic}"[/bold] '
            f'(depth={context.depth})'
        )

        system = RESEARCHER_SYSTEM.format(num_findings=num_findings)

        raw_text = self.call(
            system=system,
            user=(
                f"Research this topic thoroughly and find key facts:\n\n"
                f"TOPIC: {context.topic}\n\n"
                f"Search for multiple angles: background, recent "
                f"developments, statistics, expert views, and impact."
            ),
            tools=[WEB_SEARCH_TOOL],
            max_tokens=cfg["max_tokens"],
        )

        context.raw_findings = self._parse_findings(raw_text)
        context.token_usage["researcher"] = self.tokens_used.copy()

        self.logger.info(
            f"Found [bold]{len(context.raw_findings)}[/bold] raw findings"
        )
        return context

    # ── Parsing ───────────────────────────────────────────────────

    def _parse_findings(self, text: str) -> list[dict]:
        """
        Parse FINDING:/SOURCE: pairs from raw agent output.
        Tolerant of minor formatting variations.
        """
        findings: list[dict] = []
        current_claim: str = ""
        current_source: str = ""

        for raw_line in text.splitlines():
            line = raw_line.strip()
            if not line:
                continue

            if line.upper().startswith("FINDING:"):
                # Save previous pair if complete
                if current_claim:
                    findings.append({
                        "claim": current_claim,
                        "source": current_source or "unknown",
                    })
                current_claim = line.split(":", 1)[1].strip()
                current_source = ""

            elif line.upper().startswith("SOURCE:") and current_claim:
                current_source = line.split(":", 1)[1].strip()
                # Immediately save — source comes right after finding
                findings.append({
                    "claim": current_claim,
                    "source": current_source,
                })
                current_claim = ""
                current_source = ""

        # Catch any trailing unpaired finding
        if current_claim:
            findings.append({
                "claim": current_claim,
                "source": current_source or "unknown",
            })

        # Deduplicate by claim text
        seen: set[str] = set()
        unique: list[dict] = []
        for f in findings:
            key = f["claim"].lower().strip()
            if key not in seen and len(key) > 5:
                seen.add(key)
                unique.append(f)

        return unique
