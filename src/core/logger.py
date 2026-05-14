from __future__ import annotations

import logging
from pathlib import Path

from rich.logging import RichHandler


def setup_logger(level: str = "INFO", log_file: str | Path | None = None) -> logging.Logger:
    logger = logging.getLogger("block_pdf")
    logger.handlers.clear()
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    rich_handler = RichHandler(rich_tracebacks=True, show_time=True, show_level=True, show_path=False)
    rich_handler.setLevel(logger.level)
    formatter = logging.Formatter("%(message)s")
    rich_handler.setFormatter(formatter)
    logger.addHandler(rich_handler)

    if log_file:
        p = Path(log_file)
        p.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(p, encoding="utf-8")
        file_handler.setLevel(logger.level)
        file_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
        logger.addHandler(file_handler)

    return logger
