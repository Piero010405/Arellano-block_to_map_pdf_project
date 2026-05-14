from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

from shapely.geometry import LineString, MultiPolygon, Polygon
from shapely.geometry.base import BaseGeometry
from shapely.ops import unary_union

from src.core.exceptions import KmlError
from src.models.block import BlockRecord


class KmlService:
    def __init__(self, settings: dict[str, Any]):
        self.settings = settings
        self.project_root = Path(settings["project_root"])
        self.kml_dir = self.project_root / settings["paths"]["kml_dir"]

    def find_kml_path(self, record: BlockRecord) -> Path:
        candidates = [
            self.kml_dir / f"{record.block_id}.kml",
            self.kml_dir / f"{record.block_id}.KML",
        ]
        for candidate in candidates:
            if candidate.exists():
                return candidate

        # Case-insensitive fallback.
        target = f"{record.block_id}.kml".lower()
        for p in self.kml_dir.glob("*.kml"):
            if p.name.lower() == target:
                return p

        raise KmlError(f"KML not found for BLOCKID={record.block_id} in {self.kml_dir}")

    def read_geometry(self, kml_path: Path) -> BaseGeometry:
        try:
            text = kml_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            text = kml_path.read_text(encoding="latin-1")

        root = ET.fromstring(text)
        geometries: list[BaseGeometry] = []

        # KML coordinates are usually inside <coordinates>lon,lat,alt lon,lat,alt</coordinates>.
        for elem in root.iter():
            if elem.tag.lower().endswith("coordinates") and elem.text:
                coords = self._parse_coordinates(elem.text)
                if len(coords) >= 3:
                    # KML block files usually contain polygons. If the ring is not explicitly
                    # closed, close it before creating the Polygon.
                    ring = coords if coords[0] == coords[-1] else coords + [coords[0]]
                    try:
                        poly = Polygon(ring)
                        if poly.is_valid and not poly.is_empty and poly.area > 0:
                            geometries.append(poly)
                            continue
                    except Exception:
                        pass

                if len(coords) >= 2:
                    line = LineString(coords)
                    if not line.is_empty:
                        geometries.append(line)

        if not geometries:
            raise KmlError(f"No valid coordinates found in KML: {kml_path}")

        # Prefer polygonal geometry if available.
        polygons = [g for g in geometries if g.geom_type in {"Polygon", "MultiPolygon"}]
        selected = polygons or geometries
        geom = unary_union(selected)
        if geom.is_empty:
            raise KmlError(f"Geometry is empty for KML: {kml_path}")
        return geom

    @staticmethod
    def _parse_coordinates(raw: str) -> list[tuple[float, float]]:
        coords: list[tuple[float, float]] = []
        raw = raw.strip()
        parts = re.split(r"\s+", raw)
        for part in parts:
            if not part.strip():
                continue
            values = part.split(",")
            if len(values) < 2:
                continue
            try:
                lon = float(values[0])
                lat = float(values[1])
                coords.append((lon, lat))
            except ValueError:
                continue
        return coords
