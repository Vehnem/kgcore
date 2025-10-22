from __future__ import annotations

from pathlib import Path
from typing import Optional, Type, TypeVar, Any, Dict, Iterable
from pydantic import BaseModel
from yaml import safe_load

T = TypeVar("T", bound="KGConfig")


class KGConfig(BaseModel):
    """Base config for kg* packages to inherit from."""
    pass


HOME_CONFIG_DIR = Path("~/.kgconf/").expanduser()


def _read_yaml(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r") as f:
        data = safe_load(f)  # handles YAML merges/anchors too
    return data or {}


def _deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deep-merge two dicts. Dicts merge recursively; for non-dicts (incl. lists),
    the override wins entirely.
    """
    out = dict(base)
    for k, v in override.items():
        if k in out and isinstance(out[k], dict) and isinstance(v, dict):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = v
    return out


class ConfigLoader:
    """
    Layered config loader with deep merging.

    Load order (low → high priority):
      1) base:   ~/.kgcore/{name}.yaml (or .yml)
      2) cwd:    ./{name}.yaml (or .yml)
      3) file:   explicit `path` if provided

    Later layers override earlier ones (deep merge).
    """
    def __init__(self, config_name: str):
        self.config_name = config_name or "kgcore"

    def _candidate_paths(self, path: Optional[str | Path]) -> Iterable[Path]:
        # explicit file (if provided) — highest priority; we’ll merge it last
        explicit = [Path(path)] if path else []

        # support both .yaml and .yml
        base = [
            HOME_CONFIG_DIR / f"{self.config_name}.yaml",
            HOME_CONFIG_DIR / f"{self.config_name}.yml",
        ]
        cwd = [
            Path.cwd() / f"{self.config_name}.yaml",
            Path.cwd() / f"{self.config_name}.yml",
        ]

        # merge order: base → cwd → explicit
        return [p for p in base + cwd + explicit if p is not None]

    def load_config(self, config_class: Type[T], path: Optional[str | Path] = None) -> T:
        merged: Dict[str, Any] = {}
        found_any = False

        for i, p in enumerate(self._candidate_paths(path)):
            d = _read_yaml(p)
            if d:
                found_any = True
                merged = _deep_merge(merged, d)

        # If nothing found, still return defaults from the model
        if not found_any and path:
            # If user provided an explicit path and we found nothing there, be explicit
            p = Path(path)
            if not p.exists():
                raise FileNotFoundError(f"Config file not found: {p}")

        return config_class(**merged)



