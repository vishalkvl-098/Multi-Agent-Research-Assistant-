"""
Colored console logger using the `rich` library.
Each agent gets its own logger with a distinct color tag.
"""
import logging
from rich.logging import RichHandler
from rich.console import Console
from rich.theme import Theme

_AGENT_COLORS = {
    "Orchestrator": "bold cyan",
    "Researcher":   "bold blue",
    "FactChecker":  "bold yellow",
    "Writer":       "bold green",
    "main":         "bold white",
}

_console = Console(theme=Theme({
    "logging.level.info":    "cyan",
    "logging.level.warning": "yellow",
    "logging.level.error":   "red bold",
}))

_loggers: dict[str, logging.Logger] = {}


def get_logger(name: str) -> logging.Logger:
    if name in _loggers:
        return _loggers[name]

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    if not logger.handlers:
        handler = RichHandler(
            console=_console,
            show_path=False,
            markup=True,
            rich_tracebacks=True,
        )
        handler.setFormatter(logging.Formatter("%(message)s"))
        logger.addHandler(handler)

    logger.propagate = False
    _loggers[name] = logger
    return logger
