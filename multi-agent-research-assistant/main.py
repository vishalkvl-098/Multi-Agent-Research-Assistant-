#!/usr/bin/env python3
"""
Multi-Agent Research Assistant — CLI entry point.

Usage:
  python main.py --topic "Your research topic here"
  python main.py --topic "AI in healthcare" --depth deep --format markdown
"""
import argparse
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# ── Validate API key before importing heavy modules ───────────────
if not os.environ.get("ANTHROPIC_API_KEY"):
    print(
        "\n❌  ANTHROPIC_API_KEY is not set.\n"
        "    Copy .env.example → .env and add your key.\n"
    )
    sys.exit(1)

from src.orchestrator import ResearchOrchestrator  # noqa: E402
from src.utils.logger import get_logger            # noqa: E402

logger = get_logger("main")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Multi-Agent Research Assistant",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --topic "Impact of AI on healthcare 2024"
  python main.py --topic "Climate tech in Southeast Asia" --depth deep
  python main.py --topic "Quantum computing" --format json --verbose
        """,
    )
    parser.add_argument(
        "--topic",
        required=True,
        help="Research topic or question to investigate",
    )
    parser.add_argument(
        "--depth",
        default="standard",
        choices=["quick", "standard", "deep"],
        help="Research depth — quick|standard|deep (default: standard)",
    )
    parser.add_argument(
        "--format",
        default="markdown",
        choices=["markdown", "json"],
        dest="output_format",
        help="Output format — markdown|json (default: markdown)",
    )
    parser.add_argument(
        "--output",
        default=os.environ.get("OUTPUT_DIR", "reports/"),
        help="Output directory (default: reports/)",
    )
    parser.add_argument(
        "--model",
        default=os.environ.get("RESEARCH_MODEL", "claude-sonnet-4-6"),
        help="Claude model to use (default: claude-sonnet-4-6)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print detailed agent reasoning",
    )
    return parser.parse_args()


def slugify(text: str, max_len: int = 50) -> str:
    """Convert topic to a safe filename slug."""
    slug = text.lower().strip()
    slug = "".join(c if c.isalnum() or c in " _-" else "" for c in slug)
    slug = "_".join(slug.split())[:max_len]
    return slug or "research_report"


def main() -> None:
    args = parse_args()

    # Ensure output directory exists
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Run the pipeline
    orchestrator = ResearchOrchestrator(
        model=args.model,
        depth=args.depth,
        verbose=args.verbose,
    )
    report = orchestrator.run(args.topic)

    # Determine output path
    slug = slugify(args.topic)
    ext = "json" if args.output_format == "json" else "md"
    out_path = output_dir / f"{slug}.{ext}"

    # Write output
    if args.output_format == "json":
        out_path.write_text(
            json.dumps(report.to_dict(), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
    else:
        content = report.markdown
        if not content.strip():
            logger.error("Writer produced an empty report.")
            sys.exit(1)
        out_path.write_text(content, encoding="utf-8")

    logger.info(f"Saved → [bold]{out_path}[/bold]")

    # Also print the report to stdout
    print("\n" + "─" * 60)
    print(report.markdown)
    print("─" * 60 + "\n")


if __name__ == "__main__":
    main()
