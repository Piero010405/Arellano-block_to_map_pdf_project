from __future__ import annotations

from pathlib import Path
from typing import Any

from src.models.block import BlockRecord
from src.utils.file_utils import ensure_dir, safe_filename


class CacheService:
    def __init__(self, settings: dict[str, Any], preview: bool = False, force: bool = False):
        self.settings = settings
        self.preview = preview
        self.force = force
        self.project_root = Path(settings["project_root"])
        self.cache_cfg = settings.get("cache", {})
        self.paths = settings["paths"]
        self.naming = settings.get("naming", {})

    def map_output_path(self, record: BlockRecord) -> Path:
        filename = self.naming.get("map_filename_template", "{block_id}.png").format(
            country=record.country,
            block_id=safe_filename(record.block_id),
        )
        folder_key = "preview_maps_dir" if self.preview else "output_maps_dir"
        return self.project_root / self.paths[folder_key] / filename

    def pdf_output_path(self, record: BlockRecord) -> Path:
        filename = self.naming.get("pdf_filename_template", "{block_id}.pdf").format(
            country=record.country,
            block_id=safe_filename(record.block_id),
        )
        folder_key = "preview_pdfs_dir" if self.preview else "output_pdfs_dir"
        return self.project_root / self.paths[folder_key] / filename

    def cache_map_path(self, record: BlockRecord) -> Path:
        filename = self.naming.get("map_filename_template", "{block_id}.png").format(
            country=record.country,
            block_id=safe_filename(record.block_id),
        )
        return self.project_root / self.paths["cache_maps_dir"] / filename

    def cache_pdf_path(self, record: BlockRecord) -> Path:
        filename = self.naming.get("pdf_filename_template", "{block_id}.pdf").format(
            country=record.country,
            block_id=safe_filename(record.block_id),
        )
        return self.project_root / self.paths["cache_pdfs_dir"] / filename

    def ensure_output_dirs(self) -> None:
        keys = [
            "output_maps_dir",
            "output_pdfs_dir",
            "preview_maps_dir",
            "preview_pdfs_dir",
            "cache_maps_dir",
            "cache_pdfs_dir",
            "cache_metadata_dir",
        ]
        for key in keys:
            if key in self.paths:
                ensure_dir(self.project_root / self.paths[key])

    def should_skip_map(self, record: BlockRecord) -> tuple[bool, Path | None, bool]:
        if self.force:
            return False, None, False
        out_path = self.map_output_path(record)
        cache_path = self.cache_map_path(record)

        if self.cache_cfg.get("use_cache", True) and cache_path.exists() and not self.preview:
            return True, cache_path, True
        if self.cache_cfg.get("skip_existing_maps", True) and out_path.exists():
            return True, out_path, False
        return False, None, False

    def should_skip_pdf(self, record: BlockRecord) -> tuple[bool, Path | None, bool]:
        if self.force:
            return False, None, False
        out_path = self.pdf_output_path(record)
        cache_path = self.cache_pdf_path(record)

        if self.cache_cfg.get("use_cache", True) and cache_path.exists() and not self.preview:
            return True, cache_path, True
        if self.cache_cfg.get("skip_existing_pdfs", True) and out_path.exists():
            return True, out_path, False
        return False, None, False

    def save_map_bytes(self, record: BlockRecord, content: bytes) -> Path:
        out_path = self.map_output_path(record)
        ensure_dir(out_path.parent)
        out_path.write_bytes(content)

        if self.cache_cfg.get("save_to_cache", True) and not self.preview:
            cache_path = self.cache_map_path(record)
            ensure_dir(cache_path.parent)
            cache_path.write_bytes(content)
        return out_path

    def save_pdf_copy_to_cache(self, record: BlockRecord, pdf_path: Path) -> None:
        if self.cache_cfg.get("save_to_cache", True) and not self.preview:
            cache_path = self.cache_pdf_path(record)
            ensure_dir(cache_path.parent)
            cache_path.write_bytes(pdf_path.read_bytes())
