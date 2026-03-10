"""
Logging setup for GSC Auto Submit.

Uses Rich for beautiful, colored terminal output.

Author: halimkun (https://github.com/halimkun)
"""

import logging
import sys

from rich.console import Console
from rich.logging import RichHandler
from rich.theme import Theme

# Custom theme for consistent colors
custom_theme = Theme({
    "info": "cyan",
    "warning": "yellow",
    "error": "bold red",
    "success": "bold green",
    "dim": "dim white",
    "highlight": "bold magenta",
    "url": "underline blue",
})

# Global console instance — use this for all direct printing
console = Console(theme=custom_theme)


def setup_logger(level: int = logging.INFO) -> None:
    """Configure root logger with Rich console handler."""
    handler = RichHandler(
        console=console,
        show_time=True,
        show_path=False,
        rich_tracebacks=True,
        tracebacks_show_locals=False,
        markup=True,
    )
    handler.setLevel(level)

    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Avoid duplicate handlers on repeated calls
    if not root_logger.handlers:
        root_logger.addHandler(handler)

    # Suppress noisy third-party loggers
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("googleapiclient").setLevel(logging.WARNING)
    logging.getLogger("google.auth").setLevel(logging.WARNING)
