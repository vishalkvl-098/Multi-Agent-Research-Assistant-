"""
WriterAgent — synthesizes verified facts into a polished Markdown report.

Responsibilities:
  - Organise facts into logical sections
  - Write at a graduate level, accessible to a general audience
  - Add inline citations linked to a References section
  - Produce clean, publish-ready Markdown
"""
from src.agents.base_agent import BaseAgent
from src.context import ResearchContext

WRITER_SYSTEM = """
You are a professional research writer and editor. You receive a
numbered list of verified facts with their sources and your job is
to produce a polished, well-structured research report in Markdown.

REPORT STRUCTURE — use exactly these sections:
# [Descriptive Title — not just the raw topic]

## Executive Summary
2-3 sentence overview of the key findings and their significance.

## Background
Context and foundational information to frame the topic.

## Key Findings
The main body of evidence, organised into logical sub-sections
with clear ## headings. Group related facts together.

## Analysis & Implications
What do these findings mean? Trends, patterns, consequences.

## Conclusion
Synthesis of the most important points and forward-looking statement.

## References
Numbered list of all sources cited, formatted as:
[N] Source name or URL

WRITING RULES:
- Use inline citations like [1], [2] throughout the body
- Write in clear, confident prose — no bullet dumps
- Each section should flow naturally into the next
- Be objective and evidence-based; avoid speculation
- Target 900-1400 words for standard depth
- Use **bold** sparingly, only for the most critical terms
- Use > blockquote for one key statistic or quote per section
- Do NOT include any meta-commentary about the report itself
"""


class WriterAgent(BaseAgent):
    def __init__(self, model: str, verbose: bool = False):
        super().__init__(model, "Writer", verbose)

    def run(self, context: ResearchContext) -> ResearchContext:
        # Use verified + flagged facts (exclude removed)
        usable = [
            f for f in context.verified_findings
            if f.get("status") in ("verified", "flagged")
        ]

        if not usable:
            self.logger.error("No usable facts to write from!")
            context.final_report = (
                f"# Research Report: {context.topic}\n\n"
                "_No verified findings available to generate a report._"
            )
            context.word_count = 0
            return context

        self.logger.info(
            f"Writing report from [bold]{len(usable)}[/bold] verified facts..."
        )

        # Build numbered fact list with caveat markers for flagged items
        fact_lines = []
        for i, f in enumerate(usable, 1):
            line = f"[{i}] {f['claim']}"
            if f.get("status") == "flagged":
                line += f"  ⚠️ (uncertain: {f.get('reason', '')})"
            line += f"\n    Source: {f.get('source', 'unknown')}"
            fact_lines.append(line)

        facts_block = "\n\n".join(fact_lines)

        report = self.call(
            system=WRITER_SYSTEM,
            user=(
                f"Write a complete research report on the following topic.\n\n"
                f"TOPIC: {context.topic}\n"
                f"DEPTH: {context.depth}\n\n"
                f"VERIFIED FACTS ({len(usable)} total):\n\n"
                f"{facts_block}\n\n"
                f"Write the full Markdown report now."
            ),
            max_tokens=5000,
        )

        context.final_report = report
        context.word_count = len(report.split())
        context.token_usage["writer"] = self.tokens_used.copy()

        self.logger.info(
            f"Report complete — "
            f"[bold]{context.word_count}[/bold] words"
        )
        return context
