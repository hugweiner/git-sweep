"""Branch restore support: record deleted branches so they can be recreated."""
from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import List, Optional

DEFAULT_RESTORE_FILE = ".git-sweep-restore.json"


@dataclass
class RestoreEntry:
    branch: str
    sha: str
    remote: Optional[str] = None
    deleted_at: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(d: dict) -> "RestoreEntry":
        return RestoreEntry(
            branch=d.get("branch", ""),
            sha=d.get("sha", ""),
            remote=d.get("remote"),
            deleted_at=d.get("deleted_at", ""),
        )


def load_restore_log(path: str = DEFAULT_RESTORE_FILE) -> List[RestoreEntry]:
    """Load existing restore log from disk."""
    p = Path(path)
    if not p.exists():
        return []
    try:
        data = json.loads(p.read_text())
        return [RestoreEntry.from_dict(e) for e in data]
    except (json.JSONDecodeError, KeyError):
        return []


def save_restore_log(entries: List[RestoreEntry], path: str = DEFAULT_RESTORE_FILE) -> None:
    """Persist restore log to disk."""
    Path(path).write_text(json.dumps([e.to_dict() for e in entries], indent=2))


def record_deletion(
    branch: str,
    sha: str,
    deleted_at: str,
    remote: Optional[str] = None,
    path: str = DEFAULT_RESTORE_FILE,
) -> RestoreEntry:
    """Append a deletion record and persist."""
    entries = load_restore_log(path)
    entry = RestoreEntry(branch=branch, sha=sha, remote=remote, deleted_at=deleted_at)
    entries.append(entry)
    save_restore_log(entries, path)
    return entry


def restore_branch(entry: RestoreEntry, dry_run: bool = False) -> bool:
    """Recreate a local branch at the recorded SHA."""
    import subprocess
    if dry_run:
        return True
    result = subprocess.run(
        ["git", "branch", entry.branch, entry.sha],
        capture_output=True,
        text=True,
    )
    return result.returncode == 0
