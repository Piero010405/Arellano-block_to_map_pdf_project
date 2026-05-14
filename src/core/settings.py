from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from src.utils.yaml_utils import deep_merge, load_yaml
from src.core.exceptions import ConfigurationError


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def load_settings(country: str, profile: str) -> dict[str, Any]:
    """Load and merge base + layout + profile + country YAML config."""
    load_dotenv(PROJECT_ROOT / ".env")

    config_dir = PROJECT_ROOT / "config"
    base = load_yaml(config_dir / "base.yaml")
    layout = load_yaml(config_dir / "layout.yaml")
    profile_cfg = load_yaml(config_dir / "profiles" / f"{profile}.yaml")

    merged = deep_merge(base, layout)
    merged = deep_merge(merged, profile_cfg)

    if country != "all":
        country_cfg_path = config_dir / "countries" / f"{country}.yaml"
        country_cfg = load_yaml(country_cfg_path)
        merged = deep_merge(merged, country_cfg)

    api_key = os.getenv("GEOAPIFY_API_KEY", "").strip()
    merged.setdefault("provider", {})["api_key"] = api_key

    # Resolve project root for downstream services.
    merged["project_root"] = str(PROJECT_ROOT)
    return merged


def get_available_countries() -> list[str]:
    countries_dir = PROJECT_ROOT / "config" / "countries"
    return sorted(p.stem for p in countries_dir.glob("*.yaml"))


def require_api_key(settings: dict[str, Any]) -> None:
    if settings.get("provider", {}).get("mock_maps"):
        return
    api_key = settings.get("provider", {}).get("api_key")
    if not api_key:
        raise ConfigurationError(
            "GEOAPIFY_API_KEY is missing. Create .env from .env.example and set your key."
        )
