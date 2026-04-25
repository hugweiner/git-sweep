"""Tie restore recording into the cleaner so deletions are automatically logged."""
from __future__ import annotations

import subprocess
from datetime import datetime, timezone
from typing import List, Optional

from git_sweep.cleaner import CleanupResult
from git_sweep.restore import record_deletion, DEFAULT_RESTORE_FILE


def _resolve_sha(branch: str) -> Optional[str]:
    """Return the current tip SHA of a local branch, or None on failure."""
    result = subprocess.run(
        ["git", "rev-parse", branch],
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        return result.stdout.strip()
    return None


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def record_cleanup_results(
    results: List[CleanupResult],
    log_path: str = DEFAULT_RESTORE_FILE,
    dry_run: bool = False,
) -> int:
    """After a cleanup run, persist restore entries for every successfully deleted branch.

    Returns the number of entries recorded.
    """
    if dry_run:
        return 0

    recorded = 0
    deleted_at = _now_iso()
    for r in results:
        if not r.success:
            continue
        sha = _resolve_sha(r.branch) or r.sha or ""
        record_deletion(
            branch=r.branch,
            sha=sha,
            deleted_at=deleted_at,
            remote=r.remote if r.remote else None,
            path=log_path,
        )
        recorded += 1
    return recorded
