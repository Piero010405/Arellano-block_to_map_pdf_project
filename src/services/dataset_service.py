from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from src.core.exceptions import DatasetError
from src.models.block import BlockRecord
from src.utils.text_utils import clean_cell, unique_join


class DatasetService:
    def __init__(self, settings: dict[str, Any]):
        self.settings = settings
        self.project_root = Path(settings["project_root"])
        self.dataset_cfg = settings.get("dataset", {})
        self.aggregation_cfg = settings.get("aggregation", {})

    def load_blocks(self) -> list[BlockRecord]:
        excel_path = self.project_root / self.settings["paths"]["excel_file"]
        if not excel_path.exists():
            raise DatasetError(f"Excel file not found: {excel_path}")

        df = pd.read_excel(excel_path)
        if self.dataset_cfg.get("normalize_columns", True):
            df.columns = [str(c).strip().upper() for c in df.columns]

        if self.dataset_cfg.get("strip_whitespace", True):
            for col in df.columns:
                if df[col].dtype == "object":
                    df[col] = df[col].map(clean_cell)

        required = [str(c).upper() for c in self.dataset_cfg.get("required_columns", [])]
        missing = [c for c in required if c not in df.columns]
        if missing:
            raise DatasetError(f"Missing required columns in {excel_path.name}: {missing}")

        id_column = str(self.dataset_cfg.get("id_column", "BLOCKID")).upper()
        df[id_column] = df[id_column].map(clean_cell)

        if self.dataset_cfg.get("drop_empty_block_ids", True):
            df = df[df[id_column] != ""].copy()

        if df.empty:
            raise DatasetError("Dataset is empty after cleaning BLOCKID values.")

        group_by = [str(c).upper() for c in self.aggregation_cfg.get("group_by", [id_column])]
        rules = {str(k).upper(): v for k, v in self.aggregation_cfg.get("rules", {}).items()}

        records: list[BlockRecord] = []
        for group_values, group in df.groupby(group_by, dropna=False, sort=False):
            if not isinstance(group_values, tuple):
                group_values = (group_values,)

            values: dict[str, Any] = {}
            # Start with configured rules.
            for col, rule in rules.items():
                if col not in group.columns:
                    continue
                if rule == "first":
                    values[col] = clean_cell(group[col].iloc[0])
                elif rule == "unique_join_comma":
                    values[col] = unique_join(group[col].tolist(), sep=", ")
                elif rule == "count":
                    values[col] = len(group)
                else:
                    values[col] = clean_cell(group[col].iloc[0])

            # Ensure group columns exist in values.
            for col, val in zip(group_by, group_values):
                values.setdefault(col, clean_cell(val))

            # Ensure table fields exist even if not in aggregation rules.
            for item in self.settings.get("table_fields", []):
                col = str(item["source"]).upper()
                if col in group.columns and col not in values:
                    values[col] = unique_join(group[col].tolist(), sep=", ")

            block_id = clean_cell(values.get(id_column, group[id_column].iloc[0]))
            records.append(
                BlockRecord(
                    country=self.settings["country"],
                    block_id=block_id,
                    values=values,
                    raw_rows_count=len(group),
                    source_excel_path=excel_path,
                )
            )

        return records

    def validate(self) -> dict[str, Any]:
        records = self.load_blocks()
        return {
            "excel_file": self.settings["paths"]["excel_file"],
            "country": self.settings["country"],
            "unique_blocks": len(records),
            "sample_block_ids": [r.block_id for r in records[:10]],
        }
