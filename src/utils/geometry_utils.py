from __future__ import annotations

from typing import Iterable

from shapely.geometry import mapping
from shapely.geometry.base import BaseGeometry


def expand_bounds(bounds: tuple[float, float, float, float], margin_ratio: float) -> tuple[float, float, float, float]:
    minx, miny, maxx, maxy = bounds
    width = max(maxx - minx, 0.0001)
    height = max(maxy - miny, 0.0001)
    mx = width * margin_ratio
    my = height * margin_ratio
    return (minx - mx, miny - my, maxx + mx, maxy + my)


def bounds_to_bbox_string(bounds: tuple[float, float, float, float]) -> str:
    minx, miny, maxx, maxy = bounds
    return f"{minx},{miny},{maxx},{maxy}"


def geometry_to_geojson_feature(geom: BaseGeometry, properties: dict | None = None) -> dict:
    return {
        "type": "Feature",
        "properties": properties or {},
        "geometry": mapping(geom),
    }


def geometry_to_feature_collection(geom: BaseGeometry, properties: dict | None = None) -> dict:
    return {
        "type": "FeatureCollection",
        "features": [geometry_to_geojson_feature(geom, properties)],
    }
