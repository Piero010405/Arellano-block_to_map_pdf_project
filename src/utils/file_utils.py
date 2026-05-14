from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable


def ensure_dir(path: str | Path) -> Path:
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def safe_filename(value: str, default: str = "file") -> str:
    text = str(value or "").strip()
    text = re.sub(r"[\\/:*?\"<>|]+", "_", text)
    text = re.sub(r"\s+", "_", text)
    text = text.strip("._ ")
    return text or default


def read_lines(path: str | Path) -> list[str]:
    p = Path(path)
    with p.open("r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]


def ensure_dirs(paths: Iterable[str | Path]) -> None:
    for path in paths:
        ensure_dir(path)
