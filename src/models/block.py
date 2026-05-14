from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from shapely.geometry.base import BaseGeometry


@dataclass
class BlockRecord:
    country: str
    block_id: str
    values: dict[str, Any]
    raw_rows_count: int = 1
    source_excel_path: Path | None = None

    def get(self, key: str, default: Any = "") -> Any:
        return self.values.get(key, default)


@dataclass
class BlockContext:
    record: BlockRecord
    kml_path: Path | None = None
    geometry: BaseGeometry | None = None
    bounds: tuple[float, float, float, float] | None = None
    map_path: Path | None = None
    pdf_path: Path | None = None
    cached_map: bool = False
    cached_pdf: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)
