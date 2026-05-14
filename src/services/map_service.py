from __future__ import annotations

from typing import Any

from src.models.block import BlockContext
from src.providers.geoapify_provider import GeoapifyProvider
from src.services.cache_service import CacheService


class MapService:
    def __init__(self, settings: dict[str, Any], cache_service: CacheService):
        self.settings = settings
        self.cache_service = cache_service
        provider_name = settings.get("provider", {}).get("name", "geoapify")
        if provider_name != "geoapify":
            raise ValueError(f"Unsupported map provider: {provider_name}")
        self.provider = GeoapifyProvider(settings)

    def ensure_map(self, ctx: BlockContext) -> BlockContext:
        skip, path, from_cache = self.cache_service.should_skip_map(ctx.record)
        if skip and path:
            ctx.map_path = path
            ctx.cached_map = from_cache
            return ctx

        if ctx.geometry is None:
            raise ValueError("BlockContext.geometry is required to render a map.")

        content = self.provider.render_block_map(ctx.record, ctx.geometry)
        ctx.map_path = self.cache_service.save_map_bytes(ctx.record, content)
        ctx.cached_map = False
        return ctx
