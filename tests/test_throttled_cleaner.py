"""Tests for git_sweep.throttled_cleaner."""

from unittest.mock import patch, MagicMock
from dataclasses import dataclass
from typing import Optional

import pytest

from git_sweep.detector import BranchInfo
from git_sweep.cleaner import CleanupResult
from git_sweep.rate_limiter import RateLimitConfig, RateLimiter
from git_sweep.throttled_cleaner import throttled_cleanup, ThrottledCleanupSummary


def _branch(name: str, is_remote: bool = False) -> BranchInfo:
    return BranchInfo(
        name=name,
        is_merged=True,
        is_stale=False,
        last_commit_date="2024-01-01",
        is_remote=is_remote,
    )


def _disabled_limiter() -> RateLimiter:
    return RateLimiter(config=RateLimitConfig(enabled=False))


def _ok(branch: BranchInfo) -> CleanupResult:
    return CleanupResult(branch=branch, success=True, dry_run=False, message="deleted")


def test_throttled_cleanup_empty_returns_empty_summary():
    summary = throttled_cleanup([], limiter=_disabled_limiter())
    assert isinstance(summary, ThrottledCleanupSummary)
    assert summary.results == []
    assert summary.total_wait_seconds == 0.0


def test_throttled_cleanup_dry_run_skips_acquire():
    branches = [_branch("feat/a"), _branch("feat/b")]
    limiter = _disabled_limiter()
    with patch("git_sweep.throttled_cleaner.delete_local_branch") as mock_del:
        mock_del.side_effect = lambda b, dry_run: _ok(b)
        summary = throttled_cleanup(branches, dry_run=True, limiter=limiter)
    assert len(summary.results) == 2
    assert summary.total_wait_seconds == 0.0


def test_throttled_cleanup_calls_delete_local_for_local_branches():
    b = _branch("fix/old", is_remote=False)
    with patch("git_sweep.throttled_cleaner.delete_local_branch") as mock_del:
        mock_del.return_value = _ok(b)
        summary = throttled_cleanup([b], dry_run=True, limiter=_disabled_limiter())
    mock_del.assert_called_once_with(b, dry_run=True)
    assert summary.results[0].success is True


def test_throttled_cleanup_calls_delete_remote_for_remote_branches():
    b = _branch("origin/old", is_remote=True)
    with patch("git_sweep.throttled_cleaner.delete_remote_branch") as mock_del:
        mock_del.return_value = _ok(b)
        summary = throttled_cleanup([b], dry_run=True, remote="origin", limiter=_disabled_limiter())
    mock_del.assert_called_once_with(b, remote="origin", dry_run=True)


def test_hard_limit_stops_after_n_deleted():
    branches = [_branch(f"feat/{i}") for i in range(6)]
    with patch("git_sweep.throttled_cleaner.delete_local_branch") as mock_del:
        mock_del.side_effect = lambda b, dry_run: _ok(b)
        summary = throttled_cleanup(branches, dry_run=True, limiter=_disabled_limiter(), hard_limit=3)
    assert len(summary.deleted) == 3
    assert summary.skipped_due_to_limit == 3


def test_summary_deleted_and_failed_properties():
    b1 = _branch("a")
    b2 = _branch("b")
    r1 = CleanupResult(branch=b1, success=True, dry_run=False, message="ok")
    r2 = CleanupResult(branch=b2, success=False, dry_run=False, message="err")
    summary = ThrottledCleanupSummary(results=[r1, r2])
    assert len(summary.deleted) == 1
    assert len(summary.failed) == 1
