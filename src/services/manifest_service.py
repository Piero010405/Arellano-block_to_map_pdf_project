from __future__ import annotations

import csv
import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any

from src.models.manifest import ManifestRow
from src.utils.file_utils import ensure_dir


class ManifestService:
    def __init__(self, settings: dict[str, Any], command_name: str):
        self.settings = settings
        self.project_root = Path(settings["project_root"])
        run_id = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        country = settings.get("country", "all")
        self.run_dir = self.project_root / settings.get("paths", {}).get("runs_dir", "runs") / f"{run_id}_{command_name}_{country}"
        ensure_dir(self.run_dir)
        self.rows: list[ManifestRow] = []
        self.errors: list[ManifestRow] = []

    def add(self, row: ManifestRow) -> None:
        self.rows.append(row)
        if row.status == "ERROR":
            self.errors.append(row)

    def save(self) -> None:
        self._write_csv(self.run_dir / "manifest.csv", self.rows)
        self._write_csv(self.run_dir / "errors.csv", self.errors)
        summary = {
            "total": len(self.rows),
            "success": sum(1 for r in self.rows if r.status == "SUCCESS"),
            "error": sum(1 for r in self.rows if r.status == "ERROR"),
            "run_dir": str(self.run_dir),
        }
        (self.run_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    def save_config_snapshot(self) -> None:
        # Save as JSON to avoid losing merged structures. Name kept explicit.
        snapshot = self.settings.copy()
        if snapshot.get("provider", {}).get("api_key"):
            snapshot["provider"] = snapshot["provider"].copy()
            snapshot["provider"]["api_key"] = "***"
        (self.run_dir / "run_config_snapshot.json").write_text(
            json.dumps(snapshot, indent=2, default=str), encoding="utf-8"
        )

    @staticmethod
    def _write_csv(path: Path, rows: list[ManifestRow]) -> None:
        fieldnames = [
            "country",
            "block_id",
            "status",
            "map_cached",
            "pdf_cached",
            "map_path",
            "pdf_path",
            "error_message",
            "start_time",
            "end_time",
            "duration_sec",
        ]
        with path.open("w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for row in rows:
                writer.writerow(row.to_dict())
