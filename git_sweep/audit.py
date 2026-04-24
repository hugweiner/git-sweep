"""Audit log for git-sweep operations."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional


_DEFAULT_AUDIT_FILE = ".git-sweep-audit.json"


@dataclass
class AuditEntry:
    timestamp: str
    action: str          # "delete_local", "delete_remote", "dry_run"
    branch: str
    remote: Optional[str] = None
    success: bool = True
    error: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "action": self.action,
            "branch": self.branch,
            "remote": self.remote,
            "success": self.success,
            "error": self.error,
        }

    @staticmethod
    def from_dict(data: dict) -> "AuditEntry":
        return AuditEntry(
            timestamp=data.get("timestamp", ""),
            action=data.get("action", ""),
            branch=data.get("branch", ""),
            remote=data.get("remote"),
            success=data.get("success", True),
            error=data.get("error"),
        )


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_audit(path: str = _DEFAULT_AUDIT_FILE) -> List[AuditEntry]:
    """Load existing audit entries from *path*; return empty list if absent."""
    p = Path(path)
    if not p.exists():
        return []
    try:
        raw = json.loads(p.read_text(encoding="utf-8"))
        return [AuditEntry.from_dict(e) for e in raw]
    except (json.JSONDecodeError, KeyError):
        return []


def save_audit(entries: List[AuditEntry], path: str = _DEFAULT_AUDIT_FILE) -> None:
    """Persist *entries* to *path* as JSON."""
    Path(path).write_text(
        json.dumps([e.to_dict() for e in entries], indent=2),
        encoding="utf-8",
    )


def record(
    action: str,
    branch: str,
    *,
    remote: Optional[str] = None,
    success: bool = True,
    error: Optional[str] = None,
    path: str = _DEFAULT_AUDIT_FILE,
) -> AuditEntry:
    """Append a single audit entry and persist the log."""
    entry = AuditEntry(
        timestamp=_now_iso(),
        action=action,
        branch=branch,
        remote=remote,
        success=success,
        error=error,
    )
    entries = load_audit(path)
    entries.append(entry)
    save_audit(entries, path)
    return entry
