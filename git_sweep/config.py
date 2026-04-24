"""Configuration management for git-sweep."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

DEFAULT_CONFIG_FILENAME = ".gitsweep.json"
DEFAULT_STALE_DAYS = 90
DEFAULT_BASE_BRANCHES = ["main", "master", "develop"]


@dataclass
class SweepConfig:
    """Configuration for git-sweep behaviour."""

    base_branches: List[str] = field(default_factory=lambda: list(DEFAULT_BASE_BRANCHES))
    stale_days: int = DEFAULT_STALE_DAYS
    protected_branches: List[str] = field(default_factory=list)
    remote: str = "origin"
    dry_run: bool = False
    delete_remote: bool = False

    def to_dict(self) -> dict:
        return {
            "base_branches": self.base_branches,
            "stale_days": self.stale_days,
            "protected_branches": self.protected_branches,
            "remote": self.remote,
            "dry_run": self.dry_run,
            "delete_remote": self.delete_remote,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SweepConfig":
        return cls(
            base_branches=data.get("base_branches", list(DEFAULT_BASE_BRANCHES)),
            stale_days=int(data.get("stale_days", DEFAULT_STALE_DAYS)),
            protected_branches=data.get("protected_branches", []),
            remote=data.get("remote", "origin"),
            dry_run=bool(data.get("dry_run", False)),
            delete_remote=bool(data.get("delete_remote", False)),
        )


def load_config(path: Optional[str] = None) -> SweepConfig:
    """Load config from file, falling back to defaults."""
    config_path = Path(path) if path else _find_config()
    if config_path is None or not config_path.exists():
        return SweepConfig()
    with config_path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    return SweepConfig.from_dict(data)


def save_config(config: SweepConfig, path: Optional[str] = None) -> Path:
    """Persist config to a JSON file."""
    config_path = Path(path) if path else Path(DEFAULT_CONFIG_FILENAME)
    with config_path.open("w", encoding="utf-8") as fh:
        json.dump(config.to_dict(), fh, indent=2)
    return config_path


def _find_config() -> Optional[Path]:
    """Walk up directories looking for a .gitsweep.json file."""
    current = Path(os.getcwd())
    for directory in [current, *current.parents]:
        candidate = directory / DEFAULT_CONFIG_FILENAME
        if candidate.exists():
            return candidate
    return None
