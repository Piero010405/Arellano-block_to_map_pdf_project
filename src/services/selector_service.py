from __future__ import annotations

import random
from pathlib import Path
from typing import Any

from src.models.block import BlockRecord
from src.services.cache_service import CacheService
from src.utils.file_utils import read_lines


class SelectorService:
    def __init__(self, settings: dict[str, Any], cache_service: CacheService):
        self.settings = settings
        self.cache_service = cache_service

    def select(
        self,
        records: list[BlockRecord],
        sample_size: int | None = None,
        offset: int | None = None,
        limit: int | None = None,
        only_missing: bool = False,
        block_ids_file: str | None = None,
    ) -> list[BlockRecord]:
        selected = records[:]

        if block_ids_file:
            wanted = set(read_lines(block_ids_file))
            selected = [r for r in selected if r.block_id in wanted]

        if only_missing:
            selected = [r for r in selected if self._is_missing(r)]

        if offset is not None:
            selected = selected[int(offset) :]

        if limit is not None:
            selected = selected[: int(limit)]

        if sample_size is not None:
            sample_size = int(sample_size)
            order = self.settings.get("selection", {}).get("sample_order", "first")
            if order == "random":
                seed = int(self.settings.get("selection", {}).get("random_seed", 42))
                rng = random.Random(seed)
                selected = selected[:]
                rng.shuffle(selected)
            selected = selected[:sample_size]

        return selected

    def _is_missing(self, record: BlockRecord) -> bool:
        map_exists = self.cache_service.cache_map_path(record).exists() or self.cache_service.map_output_path(record).exists()
        pdf_exists = self.cache_service.cache_pdf_path(record).exists() or self.cache_service.pdf_output_path(record).exists()
        return not (map_exists and pdf_exists)
