"""
ResearchOrchestrator — coordinates the full multi-agent pipeline.

Flow:  ResearcherAgent → FactCheckerAgent → WriterAgent
State: shared via a single ResearchContext instance
"""
import time

from rich.console import Console
from rich.panel import Panel
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
)

from src.context import ResearchContext
from src.agents.researcher import ResearcherAgent
from src.agents.fact_checker import FactCheckerAgent
from src.agents.writer import WriterAgent
from src.utils.logger import get_logger

console = Console()


class ResearchOrchestrator:
    def __init__(
        self,
        model: str = "claude-sonnet-4-6",
        depth: str = "standard",
        verbose: bool = False,
    ):
        self.model = model
        self.depth = depth
        self.verbose = verbose
        self.logger = get_logger("Orchestrator")

        self.researcher = ResearcherAgent(model, verbose)
        self.fact_checker = FactCheckerAgent(model, verbose)
        self.writer = WriterAgent(model, verbose)

    def run(self, topic: str) -> ResearchContext:
        """
        Run the full research pipeline for the given topic.
        Returns a populated ResearchContext with the final report.
        """
        self._print_header(topic)
        ctx = ResearchContext(topic=topic, depth=self.depth)
        start = time.time()

        steps = [
            ("🔍  Researching", self.researcher.run),
            ("✅  Fact-checking", self.fact_checker.run),
            ("✍️  Writing report", self.writer.run),
        ]

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            TimeElapsedColumn(),
            console=console,
            transient=True,
        ) as progress:
            for label, fn in steps:
                task = progress.add_task(label, total=None)
                ctx = fn(ctx)
                progress.update(task, completed=True)

        ctx.elapsed = time.time() - start
        ctx.source_count = len({
            f.get("source", "")
            for f in ctx.verified_findings
            if f.get("source") and f["source"] != "unknown"
        })

        self._print_summary(ctx)
        return ctx

    # ── Display helpers ───────────────────────────────────────────

    def _print_header(self, topic: str) -> None:
        console.print()
        console.print(
            Panel(
                f"[bold cyan]Multi-Agent Research Assistant[/bold cyan]\n"
                f"[dim]Topic:[/dim] {topic}\n"
                f"[dim]Depth:[/dim] {self.depth}  "
                f"[dim]Model:[/dim] {self.model}",
                border_style="cyan",
                padding=(0, 2),
            )
        )
        console.print()

    def _print_summary(self, ctx: ResearchContext) -> None:
        console.print()
        console.print(
            Panel(
                f"[bold green]✅ Report Ready[/bold green]\n\n"
                f"  [dim]Time    :[/dim] {ctx.elapsed:.1f}s\n"
                f"  [dim]Words   :[/dim] {ctx.word_count}\n"
                f"  [dim]Sources :[/dim] {ctx.source_count}\n"
                f"  [dim]Facts   :[/dim] {ctx.verified_count} verified",
                border_style="green",
                padding=(0, 2),
            )
        )
        console.print()

        # Token usage breakdown
        if ctx.token_usage:
            total_in = sum(
                v.get("input", 0) for v in ctx.token_usage.values()
            )
            total_out = sum(
                v.get("output", 0) for v in ctx.token_usage.values()
            )
            self.logger.info(
                f"Token usage — input: {total_in:,}  output: {total_out:,}"
            )
