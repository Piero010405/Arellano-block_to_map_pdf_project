from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class ManifestRow:
    country: str
    block_id: str
    status: str
    map_cached: bool = False
    pdf_cached: bool = False
    map_path: str = ""
    pdf_path: str = ""
    error_message: str = ""
    start_time: str = ""
    end_time: str = ""
    duration_sec: float = 0.0

    def to_dict(self) -> dict:
        return asdict(self)


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")
