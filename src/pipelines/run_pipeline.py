from __future__ import annotations

import time
from typing import Any

from rich.console import Console
from tqdm import tqdm

from src.core.exceptions import BlockPdfError
from src.core.logger import setup_logger
from src.core.settings import require_api_key
from src.models.block import BlockContext
from src.models.manifest import ManifestRow, now_iso
from src.services.cache_service import CacheService
from src.services.dataset_service import DatasetService
from src.services.kml_service import KmlService
from src.services.manifest_service import ManifestService
from src.services.map_service import MapService
from src.services.pdf_service import PdfService
from src.services.selector_service import SelectorService

console = Console()


def run_country_pipeline(
    settings: dict[str, Any],
    *,
    command_name: str,
    preview: bool = False,
    sample_size: int | None = None,
    offset: int | None = None,
    limit: int | None = None,
    only_missing: bool = False,
    block_ids_file: str | None = None,
    force: bool = False,
) -> dict[str, Any]:
    logger = setup_logger(settings.get("logging", {}).get("level", "INFO"))
    require_api_key(settings)

    cache_service = CacheService(settings, preview=preview, force=force)
    cache_service.ensure_output_dirs()

    manifest = ManifestService(settings, command_name=command_name)
    manifest.save_config_snapshot()

    dataset_service = DatasetService(settings)
    records = dataset_service.load_blocks()

    selector = SelectorService(settings, cache_service)
    if sample_size is None and preview:
        sample_size = int(settings.get("selection", {}).get("sample_size") or 10)

    selected = selector.select(
        records,
        sample_size=sample_size,
        offset=offset,
        limit=limit,
        only_missing=only_missing,
        block_ids_file=block_ids_file,
    )

    logger.info(f"Country={settings['country']} | total_blocks={len(records)} | selected={len(selected)}")

    kml_service = KmlService(settings)
    map_service = MapService(settings, cache_service)
    pdf_service = PdfService(settings, cache_service)

    for record in tqdm(selected, desc=f"{settings['country']} blocks"):
        start = time.time()
        start_iso = now_iso()
        row = ManifestRow(country=record.country, block_id=record.block_id, status="PENDING")
        row.start_time = start_iso
        try:
            ctx = BlockContext(record=record)
            ctx.kml_path = kml_service.find_kml_path(record)
            ctx.geometry = kml_service.read_geometry(ctx.kml_path)
            ctx.bounds = ctx.geometry.bounds
            ctx = map_service.ensure_map(ctx)
            ctx = pdf_service.ensure_pdf(ctx)

            row.status = "SUCCESS"
            row.map_cached = ctx.cached_map
            row.pdf_cached = ctx.cached_pdf
            row.map_path = str(ctx.map_path or "")
            row.pdf_path = str(ctx.pdf_path or "")
        except Exception as exc:
            row.status = "ERROR"
            row.error_message = str(exc)
            logger.error(f"BLOCKID={record.block_id} failed: {exc}")
            if settings.get("processing", {}).get("stop_on_error", False):
                raise
        finally:
            row.end_time = now_iso()
            row.duration_sec = round(time.time() - start, 3)
            manifest.add(row)

    manifest.save()
    summary = {
        "country": settings.get("country"),
        "selected": len(selected),
        "success": sum(1 for r in manifest.rows if r.status == "SUCCESS"),
        "error": sum(1 for r in manifest.rows if r.status == "ERROR"),
        "run_dir": str(manifest.run_dir),
    }
    console.print(summary)
    return summary
