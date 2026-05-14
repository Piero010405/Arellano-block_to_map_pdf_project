from __future__ import annotations

from pathlib import Path
from typing import Any

from rich.console import Console
from rich.table import Table

from src.services.dataset_service import DatasetService
from src.services.kml_service import KmlService

console = Console()


def validate_country(settings: dict[str, Any]) -> dict[str, Any]:
    dataset_service = DatasetService(settings)
    records = dataset_service.load_blocks()
    kml_service = KmlService(settings)

    missing = []
    existing = 0
    for record in records:
        try:
            kml_service.find_kml_path(record)
            existing += 1
        except Exception:
            missing.append(record.block_id)

    result = {
        "country": settings["country"],
        "unique_blocks": len(records),
        "kml_existing": existing,
        "kml_missing": len(missing),
        "missing_sample": missing[:20],
    }

    table = Table(title=f"Validation - {settings['country']}")
    table.add_column("Metric")
    table.add_column("Value")
    for k, v in result.items():
        table.add_row(k, str(v))
    console.print(table)
    return result
