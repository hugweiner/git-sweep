"""Reporter: format branch tables and cleanup results for terminal output."""

from __future__ import annotations

from typing import List

from git_sweep.cleaner import CleanupResult
from git_sweep.snapshot import Snapshot

_COL_NAME = 40
_COL_DATE = 20
_COL_FLAG = 10


def format_branch_table(branches) -> str:  # branches: List[BranchInfo]
    if not branches:
        return "No branches found."
    header = (
        f"{'BRANCH':<{_COL_NAME}} {'LAST COMMIT':<{_COL_DATE}}"
        f" {'MERGED':<{_COL_FLAG}} {'STALE':<{_COL_FLAG}}"
    )
    sep = "-" * len(header)
    rows = [header, sep]
    for b in branches:
        date_str = b.last_commit.strftime("%Y-%m-%d") if b.last_commit else "unknown"
        rows.append(
            f"{b.name:<{_COL_NAME}} {date_str:<{_COL_DATE}}"
            f" {'yes' if b.is_merged else 'no':<{_COL_FLAG}}"
            f" {'yes' if b.is_stale else 'no':<{_COL_FLAG}}"
        )
    return "\n".join(rows)


def format_cleanup_results(results: List[CleanupResult]) -> str:
    if not results:
        return "Nothing to clean up."
    lines = []
    for r in results:
        status = "OK" if r.success else "FAILED"
        dry = " [dry-run]" if r.dry_run else ""
        msg = f" ({r.message})" if r.message else ""
        lines.append(f"  [{status}]{dry} {r.branch}{msg}")
    ok = sum(1 for r in results if r.success)
    lines.append(f"\n{ok}/{len(results)} branches cleaned up.")
    return "\n".join(lines)


def format_snapshot_diff(old: Snapshot, new: Snapshot) -> str:
    """Summarise what changed between two snapshots."""
    diff = new.diff(old)
    lines = [f"Snapshot diff ({old.captured_at} -> {new.captured_at})"]
    if diff["added"]:
        lines.append("  New branches detected:")
        for name in diff["added"]:
            lines.append(f"    + {name}")
    if diff["removed"]:
        lines.append("  Branches no longer present:")
        for name in diff["removed"]:
            lines.append(f"    - {name}")
    if not diff["added"] and not diff["removed"]:
        lines.append("  No changes detected.")
    return "\n".join(lines)
