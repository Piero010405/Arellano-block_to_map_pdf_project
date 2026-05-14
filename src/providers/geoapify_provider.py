from __future__ import annotations

import io
import time
from typing import Any

import requests
from PIL import Image, ImageDraw, ImageFont
from shapely.geometry.base import BaseGeometry
from tenacity import retry, stop_after_attempt, wait_exponential

from src.core.exceptions import MapProviderError
from src.models.block import BlockRecord
from src.providers.base_map_provider import BaseMapProvider
from src.utils.geometry_utils import (
    bounds_to_bbox_string,
    expand_bounds,
    geometry_to_feature_collection,
)


class GeoapifyProvider(BaseMapProvider):
    """Geoapify Static Maps provider.

    The provider uses POST because large polygons can exceed URL length limits.
    """

    def __init__(self, settings: dict[str, Any]):
        self.settings = settings
        self.provider_cfg = settings.get("provider", {})
        self.map_cfg = settings.get("map", {})
        self.api_key = self.provider_cfg.get("api_key", "")
        self.endpoint = self.provider_cfg.get("endpoint", "https://maps.geoapify.com/v1/staticmap")
        self.timeout = int(self.provider_cfg.get("timeout_seconds", 60))
        self.requests_per_second = float(self.provider_cfg.get("requests_per_second", 2))
        self._last_request = 0.0

    def render_block_map(self, record: BlockRecord, geometry: BaseGeometry) -> bytes:
        if self.provider_cfg.get("mock_maps", False):
            return self._mock_map(record, geometry)

        self._rate_limit()
        payload = self._build_payload(record, geometry)
        return self._post_static_map(payload)

    def _rate_limit(self) -> None:
        if self.requests_per_second <= 0:
            return
        min_interval = 1.0 / self.requests_per_second
        elapsed = time.time() - self._last_request
        if elapsed < min_interval:
            time.sleep(min_interval - elapsed)
        self._last_request = time.time()

    def _build_payload(self, record: BlockRecord, geometry: BaseGeometry) -> dict[str, Any]:
        width = int(self.map_cfg.get("width", 1280))
        height = int(self.map_cfg.get("height", 900))
        margin_ratio = float(self.map_cfg.get("margin_ratio", 0.15))
        simplify_tol = self.map_cfg.get("geometry_simplify_tolerance", None)

        geom = geometry
        if simplify_tol is not None and float(simplify_tol) > 0:
            geom = geom.simplify(float(simplify_tol), preserve_topology=True)

        polygon_cfg = self.map_cfg.get("polygon", {})
        properties = {
            "stroke": polygon_cfg.get("stroke_color", "#FF0000"),
            "stroke-width": int(polygon_cfg.get("stroke_width", 3)),
            "fill": polygon_cfg.get("fill_color", "#FF0000"),
            "fill-opacity": float(polygon_cfg.get("fill_opacity", 0.15)),
        }

        payload: dict[str, Any] = {
            "style": self.map_cfg.get("style", "osm-bright"),
            "width": width,
            "height": height,
            "scaleFactor": int(self.map_cfg.get("scale_factor", 1)),
            "geojson": geometry_to_feature_collection(geom, properties=properties),
        }

        if self.map_cfg.get("fit_to_geometry", True):
            payload["bbox"] = bounds_to_bbox_string(expand_bounds(geom.bounds, margin_ratio))
        else:
            centroid = geom.centroid
            payload["center"] = f"lonlat:{centroid.x},{centroid.y}"
            payload["zoom"] = int(self.map_cfg.get("zoom") or 17)

        return payload

    @retry(wait=wait_exponential(multiplier=1, min=1, max=10), stop=stop_after_attempt(3))
    def _post_static_map(self, payload: dict[str, Any]) -> bytes:
        params = {"apiKey": self.api_key}
        headers = {"Content-Type": "application/json"}
        response = requests.post(
            self.endpoint,
            params=params,
            json=payload,
            headers=headers,
            timeout=self.timeout,
        )
        if response.status_code >= 400:
            raise MapProviderError(
                f"Geoapify error {response.status_code}: {response.text[:500]}"
            )
        content_type = response.headers.get("Content-Type", "")
        if "image" not in content_type.lower() and not response.content.startswith(b"\x89PNG"):
            raise MapProviderError(
                f"Geoapify did not return an image. Content-Type={content_type}. Body={response.text[:500]}"
            )
        return response.content

    def _mock_map(self, record: BlockRecord, geometry: BaseGeometry) -> bytes:
        width = int(self.map_cfg.get("width", 1280))
        height = int(self.map_cfg.get("height", 900))
        img = Image.new("RGB", (width, height), "white")
        draw = ImageDraw.Draw(img)
        draw.rectangle([20, 20, width - 20, height - 20], outline="black", width=3)
        draw.text((50, 50), f"MOCK MAP - {record.country.upper()} - {record.block_id}", fill="black")
        draw.text((50, 90), f"Bounds: {geometry.bounds}", fill="black")
        draw.text((50, 130), "Set provider.mock_maps=false and GEOAPIFY_API_KEY to render real maps.", fill="black")
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        return buffer.getvalue()
