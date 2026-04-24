"""Tests for git_sweep.cleaner and git_sweep.reporter."""

from datetime import datetime, timezone
from unittest.mock import patch

import pytest

from git_sweep.cleaner import CleanupResult, cleanup_branches, delete_local_branch, delete_remote_branch
from git_sweep.detector import BranchInfo
from git_sweep.reporter import format_branch_table, format_cleanup_results


def make_branch(name, merged=True, stale=False, remote=None):
    return BranchInfo(
        name=name,
        is_merged=merged,
        is_stale=stale,
        remote=remote,
        last_commit_date=datetime(2024, 1, 15, tzinfo=timezone.utc),
    )


@patch("git_sweep.cleaner._run_git", return_value=("Deleted branch feature/x.", "", 0))
def test_delete_local_branch_success(mock_git):
    result = delete_local_branch("feature/x")
    assert result.success is True
    assert result.error is None
    mock_git.assert_called_once_with(["branch", "-d", "feature/x"])


@patch("git_sweep.cleaner._run_git", return_value=("", "error: branch not found", 1))
def test_delete_local_branch_failure(mock_git):
    result = delete_local_branch("feature/x")
    assert result.success is False
    assert "branch not found" in result.error


def test_delete_local_branch_dry_run():
    result = delete_local_branch("feature/x", dry_run=True)
    assert result.success is True
    assert result.dry_run is True


@patch("git_sweep.cleaner._run_git", return_value=("", "", 0))
def test_delete_remote_branch_success(mock_git):
    result = delete_remote_branch("feature/x", remote="origin")
    assert result.success is True
    assert result.remote == "origin"
    mock_git.assert_called_once_with(["push", "origin", "--delete", "feature/x"])


@patch("git_sweep.cleaner._run_git", return_value=("Deleted.", "", 0))
def test_cleanup_branches_skips_remote_when_not_requested(mock_git):
    branches = [make_branch("feature/a", remote="origin")]
    results = cleanup_branches(branches, delete_remote=False)
    assert len(results) == 1
    assert results[0].remote is None


@patch("git_sweep.cleaner._run_git", return_value=("Deleted.", "", 0))
def test_cleanup_branches_includes_remote(mock_git):
    branches = [make_branch("feature/a", remote="origin")]
    results = cleanup_branches(branches, delete_remote=True)
    assert len(results) == 2
    assert any(r.remote == "origin" for r in results)


def test_format_branch_table_empty():
    output = format_branch_table([])
    assert "No branches" in output


def test_format_branch_table_with_branches():
    branches = [make_branch("feature/old", merged=True, stale=True)]
    output = format_branch_table(branches)
    assert "feature/old" in output
    assert "yes" in output


def test_format_cleanup_results_dry_run():
    results = [CleanupResult(branch="feature/x", remote=None, success=True, dry_run=True)]
    output = format_cleanup_results(results)
    assert "dry-run" in output
    assert "would be deleted" in output


def test_format_cleanup_results_mixed():
    results = [
        CleanupResult(branch="feature/a", remote=None, success=True),
        CleanupResult(branch="feature/b", remote=None, success=False, error="locked"),
    ]
    output = format_cleanup_results(results)
    assert "deleted" in output
    assert "failed" in output
    assert "locked" in output
