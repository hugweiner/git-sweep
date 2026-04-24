"""Snapshot: capture and persist branch state for diffing across runs."""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Dict, List, Optional

DEFAULT_SNAPSHOT_PATH = ".git-sweep-snapshot.json"


@dataclass
class BranchSnapshot:
    name: str
    last_commit: str  # ISO-8601 date string
    is_merged: bool
    is_stale: bool


@dataclass
class Snapshot:
    captured_at: str  # ISO-8601 datetime
    base_branch: str
    branches: List[BranchSnapshot]

    def branch_names(self) -> List[str]:
        return [b.name for b in self.branches]

    def diff(self, other: "Snapshot") -> Dict[str, List[str]]:
        """Return branches added/removed compared to *other* (older) snapshot."""
        prev = set(other.branch_names())
        curr = set(self.branch_names())
        return {
            "added": sorted(curr - prev),
            "removed": sorted(prev - curr),
        }


def capture_snapshot(
    branches,  # Iterable[BranchInfo] from detector
    base_branch: str,
) -> Snapshot:
    """Build a Snapshot from live BranchInfo objects."""
    snaps = [
        BranchSnapshot(
            name=b.name,
            last_commit=b.last_commit.isoformat() if b.last_commit else "",
            is_merged=b.is_merged,
            is_stale=b.is_stale,
        )
        for b in branches
    ]
    return Snapshot(
        captured_at=datetime.utcnow().isoformat(),
        base_branch=base_branch,
        branches=snaps,
    )


def save_snapshot(snapshot: Snapshot, path: str = DEFAULT_SNAPSHOT_PATH) -> None:
    data = {
        "captured_at": snapshot.captured_at,
        "base_branch": snapshot.base_branch,
        "branches": [asdict(b) for b in snapshot.branches],
    }
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2)


def load_snapshot(path: str = DEFAULT_SNAPSHOT_PATH) -> Optional[Snapshot]:
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    branches = [
        BranchSnapshot(
            name=b["name"],
            last_commit=b.get("last_commit", ""),
            is_merged=b.get("is_merged", False),
            is_stale=b.get("is_stale", False),
        )
        for b in data.get("branches", [])
    ]
    return Snapshot(
        captured_at=data.get("captured_at", ""),
        base_branch=data.get("base_branch", "main"),
        branches=branches,
    )
