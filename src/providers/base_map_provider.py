from __future__ import annotations

from abc import ABC, abstractmethod

from shapely.geometry.base import BaseGeometry

from src.models.block import BlockRecord


class BaseMapProvider(ABC):
    @abstractmethod
    def render_block_map(self, record: BlockRecord, geometry: BaseGeometry) -> bytes:
        """Return PNG bytes for a block map."""
        raise NotImplementedError
