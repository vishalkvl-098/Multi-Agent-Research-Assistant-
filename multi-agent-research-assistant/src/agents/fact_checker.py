"""
FactCheckerAgent — validates every claim from the Researcher.

Responsibilities:
  - Check internal consistency (do claims contradict each other?)
  - Assess plausibility against well-known facts
  - Remove or flag dubious, vague, or contradictory claims
  - Return a cleaned list ready for the Writer
"""
import json
import re
from src.agents.base_agent import BaseAgent
from src.context import ResearchContext

FACT_CHECKER_SYSTEM = """
You are an expert fact-checking agent. You receive a numbered list
of research claims with their sources. Your job is to validate each
one carefully.

For every claim, assess:
1. INTERNAL CONSISTENCY — does it contradict other claims in the list?
2. PLAUSIBILITY — does it align with broadly accepted knowledge?
3. SPECIFICITY — is it a concrete fact (not vague or generic)?
4. SOURCE QUALITY — is the source credible (not "unknown")?

STATUS options:
  "verified"  — claim is plausible, specific, and consistent
  "flagged"   — claim is uncertain or needs caveat; keep with note
  "removed"   — claim is false, contradictory, or too vague to use

RESPOND ONLY with a valid JSON array. No preamble, no markdown fences.
Each element must have exactly these keys:
  "claim"   : string  (original claim text)
  "source"  : string  (original source)
  "status"  : "verified" | "flagged" | "removed"
  "reason"  : string  (brief explanation; empty string if verified)

Example:
[
  {
    "claim": "Global EV sales reached 14 million units in 2023.",
    "source": "https://iea.org/ev-outlook",
    "status": "verified",
    "reason": ""
  },
  {
    "claim": "EVs will completely replace combustion engines by 2025.",
    "source": "unknown",
    "status": "removed",
    "reason": "Overly speculative and contradicted by other findings."
  }
]
"""


class FactCheckerAgent(BaseAgent):
    def __init__(self, model: str, verbose: bool = False):
        super().__init__(model, "FactChecker", verbose)

    def run(self, context: ResearchContext) -> ResearchContext:
        if not context.raw_findings:
            self.logger.warning("No findings to validate — skipping.")
            context.verified_findings = []
            return context

        self.logger.info(
            f"Validating [bold]{len(context.raw_findings)}[/bold] claims..."
        )

        # Format numbered list for the prompt
        findings_text = "\n".join(
            f"{i+1}. CLAIM: {f['claim']}\n   SOURCE: {f.get('source','unknown')}"
            for i, f in enumerate(context.raw_findings)
        )

        raw_response = self.call(
            system=FACT_CHECKER_SYSTEM,
            user=(
                f"Fact-check these {len(context.raw_findings)} research "
                f"claims about: {context.topic}\n\n{findings_text}"
            ),
            max_tokens=3500,
        )

        context.verified_findings = self._parse_results(
            raw_response, context.raw_findings
        )
        context.token_usage["fact_checker"] = self.tokens_used.copy()

        verified = sum(
            1 for f in context.verified_findings
            if f["status"] == "verified"
        )
        flagged = sum(
            1 for f in context.verified_findings
            if f["status"] == "flagged"
        )
        removed = sum(
            1 for f in context.verified_findings
            if f["status"] == "removed"
        )

        self.logger.info(
            f"[green]{verified} verified[/green]  "
            f"[yellow]{flagged} flagged[/yellow]  "
            f"[red]{removed} removed[/red]"
        )
        return context

    # ── Parsing ───────────────────────────────────────────────────

    def _parse_results(
        self,
        text: str,
        original_findings: list[dict],
    ) -> list[dict]:
        """
        Extract JSON from the model response robustly.
        Falls back to marking all originals as verified if parsing fails.
        """
        # Strip any accidental markdown fences
        cleaned = re.sub(r"```(?:json)?", "", text).strip()

        # Find the outermost JSON array
        start = cleaned.find("[")
        end = cleaned.rfind("]") + 1

        if start == -1 or end == 0:
            self.logger.warning(
                "Could not locate JSON array in response — "
                "passing all findings through as verified."
            )
            return self._fallback(original_findings)

        try:
            results: list[dict] = json.loads(cleaned[start:end])
            # Validate structure
            validated = []
            for item in results:
                if not isinstance(item, dict):
                    continue
                validated.append({
                    "claim":  str(item.get("claim",  "")),
                    "source": str(item.get("source", "unknown")),
                    "status": item.get("status", "verified")
                              if item.get("status") in
                              ("verified", "flagged", "removed")
                              else "verified",
                    "reason": str(item.get("reason", "")),
                })
            return validated

        except json.JSONDecodeError as e:
            self.logger.warning(
                f"JSON decode error ({e}) — falling back to originals."
            )
            return self._fallback(original_findings)

    @staticmethod
    def _fallback(findings: list[dict]) -> list[dict]:
        """Return all original findings as 'verified' on parse failure."""
        return [
            {
                "claim":  f.get("claim", ""),
                "source": f.get("source", "unknown"),
                "status": "verified",
                "reason": "",
            }
            for f in findings
        ]
