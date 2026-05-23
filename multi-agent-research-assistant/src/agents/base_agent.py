"""
BaseAgent — abstract base class shared by all research agents.

Handles:
  - Anthropic client setup
  - Retry logic with exponential back-off
  - Token usage tracking
  - Text extraction from API responses
"""
import os
import time
from abc import ABC, abstractmethod
from typing import Optional

import anthropic

from src.utils.logger import get_logger


class BaseAgent(ABC):
    def __init__(
        self,
        model: str,
        name: str,
        verbose: bool = False,
        max_retries: int = 3,
    ):
        self.model = model
        self.name = name
        self.verbose = verbose
        self.max_retries = max_retries
        self.client = anthropic.Anthropic(
            api_key=os.environ.get("ANTHROPIC_API_KEY")
        )
        self.logger = get_logger(name)
        self._tokens_used: dict[str, int] = {
            "input": 0, "output": 0
        }

    # ── Public API ────────────────────────────────────────────────

    def call(
        self,
        system: str,
        user: str,
        tools: Optional[list] = None,
        max_tokens: int = 2048,
    ) -> str:
        """
        Call the Claude API with retry logic.
        Returns the full text content of the response.
        """
        kwargs: dict = dict(
            model=self.model,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        if tools:
            kwargs["tools"] = tools

        last_error: Optional[Exception] = None

        for attempt in range(1, self.max_retries + 1):
            try:
                response = self.client.messages.create(**kwargs)
                self._track_usage(response)
                text = self._extract_text(response)
                if self.verbose:
                    self.logger.debug(
                        f"[dim]Response ({len(text)} chars)[/dim]"
                    )
                return text

            except anthropic.RateLimitError as e:
                wait = 2 ** attempt
                self.logger.warning(
                    f"Rate limited. Waiting {wait}s (attempt {attempt}/{self.max_retries})"
                )
                time.sleep(wait)
                last_error = e

            except anthropic.APIError as e:
                wait = 2 ** attempt
                self.logger.warning(
                    f"API error: {e}. Retrying in {wait}s (attempt {attempt}/{self.max_retries})"
                )
                time.sleep(wait)
                last_error = e

            except Exception as e:
                self.logger.error(f"Unexpected error: {e}")
                raise

        raise RuntimeError(
            f"{self.name} failed after {self.max_retries} retries. "
            f"Last error: {last_error}"
        )

    @property
    def tokens_used(self) -> dict[str, int]:
        return self._tokens_used

    # ── Abstract ──────────────────────────────────────────────────

    @abstractmethod
    def run(self, *args, **kwargs):
        """Each agent implements its own run() method."""
        ...

    # ── Private helpers ───────────────────────────────────────────

    def _extract_text(self, response) -> str:
        """Pull all text blocks from an API response."""
        parts = []
        for block in response.content:
            if hasattr(block, "text"):
                parts.append(block.text)
        return "\n".join(parts).strip()

    def _track_usage(self, response) -> None:
        if hasattr(response, "usage"):
            self._tokens_used["input"] += getattr(
                response.usage, "input_tokens", 0
            )
            self._tokens_used["output"] += getattr(
                response.usage, "output_tokens", 0
            )
