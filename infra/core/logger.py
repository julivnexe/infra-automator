"""Rich-powered console + structured file logging.

A single Console instance is shared across the app so colour/redirection
behaves consistently. File logs land in ``./logs/infra.log`` so that long
provisioning runs leave an audit trail even after the terminal scrolls away.
"""

from __future__ import annotations

import logging
from pathlib import Path

from rich.console import Console
from rich.logging import RichHandler

console = Console()

_LOG_DIR = Path("logs")
_LOG_FILE = _LOG_DIR / "infra.log"


def setup_logging(verbose: bool = False) -> logging.Logger:
    """Configure root logger with a Rich console handler + rotating file handler."""
    level = logging.DEBUG if verbose else logging.INFO

    _LOG_DIR.mkdir(exist_ok=True)

    logger = logging.getLogger("infra")
    logger.setLevel(level)
    logger.handlers.clear()

    rich_handler = RichHandler(
        console=console,
        rich_tracebacks=True,
        show_time=False,
        show_path=False,
        markup=True,
    )
    rich_handler.setLevel(level)
    logger.addHandler(rich_handler)

    file_handler = logging.FileHandler(_LOG_FILE, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    )
    logger.addHandler(file_handler)

    logger.propagate = False
    return logger


def get_logger() -> logging.Logger:
    return logging.getLogger("infra")
