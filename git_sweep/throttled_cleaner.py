"""Throttled branch cleanup that respects rate limits."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from git_sweep.cleaner import CleanupResult, delete_local_branch, delete_remote_branch
from git_sweep.detector import BranchInfo
from git_sweep.rate_limiter import RateLimiter, get_default_limiter


@dataclass
class ThrottledCleanupSummary:
    results: List[CleanupResult] = field(default_factory=list)
    total_wait_seconds: float = 0.0
    skipped_due_to_limit: int = 0

    @property
    def deleted(self) -> List[CleanupResult]:
        return [r for r in self.results if r.success]

    @property
    def failed(self) -> List[CleanupResult]:
        return [r for r in self.results if not r.success and not r.dry_run]


def throttled_cleanup(
    branches: List[BranchInfo],
    dry_run: bool = False,
    remote: Optional[str] = None,
    limiter: Optional[RateLimiter] = None,
    hard_limit: Optional[int] = None,
) -> ThrottledCleanupSummary:
    """Delete branches with rate limiting applied between each operation."""
    if limiter is None:
        limiter = get_default_limiter()

    summary = ThrottledCleanupSummary()

    for branch in branches:
        if hard_limit is not None and len(summary.deleted) >= hard_limit:
            summary.skipped_due_to_limit += 1
            continue

        if not dry_run:
            wait = limiter.acquire()
            summary.total_wait_seconds += wait

        if branch.is_remote and remote:
            result = delete_remote_branch(branch, remote=remote, dry_run=dry_run)
        else:
            result = delete_local_branch(branch, dry_run=dry_run)

        summary.results.append(result)

    return summary
