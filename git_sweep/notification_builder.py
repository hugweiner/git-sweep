"""Build human-readable notification messages from sweep results."""
from __future__ import annotations

from typing import Sequence

from git_sweep.cleaner import CleanupResult
from git_sweep.snapshot import Snapshot

_SUBJECT_TEMPLATE = "[git-sweep] {deleted} branch(es) cleaned up in {repo}"


def build_subject(results: Sequence[CleanupResult], repo: str = "repo") -> str:
    deleted = sum(1 for r in results if r.deleted)
    return _SUBJECT_TEMPLATE.format(deleted=deleted, repo=repo)


def build_body(
    results: Sequence[CleanupResult],
    before: Snapshot | None = None,
    after: Snapshot | None = None,
    dry_run: bool = False,
) -> str:
    lines: list[str] = []
    mode = "(DRY RUN) " if dry_run else ""
    lines.append(f"{mode}git-sweep cleanup report")
    lines.append("=" * 40)

    deleted = [r for r in results if r.deleted]
    failed = [r for r in results if not r.deleted and r.error]
    skipped = [r for r in results if not r.deleted and not r.error]

    if deleted:
        lines.append(f"\nDeleted ({len(deleted)}):")
        for r in deleted:
            scope = f"{r.scope}: " if r.scope else ""
            lines.append(f"  - {scope}{r.branch}")

    if failed:
        lines.append(f"\nFailed ({len(failed)}):")
        for r in failed:
            lines.append(f"  - {r.branch}: {r.error}")

    if skipped:
        lines.append(f"\nSkipped ({len(skipped)}):")
        for r in skipped:
            lines.append(f"  - {r.branch}")

    if before is not None and after is not None:
        before_names = before.branch_names()
        after_names = after.branch_names()
        removed = sorted(before_names - after_names)
        if removed:
            lines.append("\nSnapshot delta (removed):")
            for name in removed:
                lines.append(f"  - {name}")

    lines.append("\n" + "=" * 40)
    return "\n".join(lines)
