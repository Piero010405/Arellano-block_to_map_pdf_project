from __future__ import annotations

import math
import pandas as pd


def clean_cell(value) -> str:
    if value is None:
        return ""
    try:
        if isinstance(value, float) and math.isnan(value):
            return ""
    except TypeError:
        pass
    if pd.isna(value):
        return ""
    return str(value).strip()


def unique_join(values, sep: str = ", ") -> str:
    seen = []
    for value in values:
        cleaned = clean_cell(value)
        if cleaned and cleaned not in seen:
            seen.append(cleaned)
    return sep.join(seen)
