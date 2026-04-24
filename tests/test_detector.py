"""Tests for git_sweep.detector module."""

from __future__ import annotations

import subprocess
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest

from git_sweep.detector import (
    BranchInfo,
    detect_branches,
    get_branch_last_commit_date,
    get_merged_branches,
)

REPO = "/fake/repo"


@patch("git_sweep.detector._run_git")
def test_get_merged_branches_excludes_base(mock_run):
    mock_run.return_value = "main\nfeature/login\nfix/typo"
    result = get_merged_branches(REPO, base_branch="main")
    assert "main" not in result
    assert "feature/login" in result
    assert "fix/typo" in result


@patch("git_sweep.detector._run_git")
def test_get_merged_branches_empty(mock_run):
    mock_run.return_value = ""
    result = get_merged_branches(REPO)
    assert result == []


@patch("git_sweep.detector._run_git")
def test_get_branch_last_commit_date_valid(mock_run):
    ts = 1_700_000_000
    mock_run.return_value = str(ts)
    result = get_branch_last_commit_date(REPO, "feature/x")
    assert isinstance(result, datetime)
    assert result.tzinfo == timezone.utc
    assert int(result.timestamp()) == ts


@patch("git_sweep.detector._run_git")
def test_get_branch_last_commit_date_error(mock_run):
    mock_run.side_effect = subprocess.CalledProcessError(128, "git")
    result = get_branch_last_commit_date(REPO, "ghost-branch")
    assert result is None


@patch("git_sweep.detector.get_branch_last_commit_date")
@patch("git_sweep.detector._run_git")
def test_detect_branches_marks_merged_and_stale(mock_run, mock_date):
    # First call: get all branches; second call: merged branches
    def run_git_side_effect(args, cwd):
        if "--merged" in args:
            return "old-feature"
        return "old-feature\nnew-feature"

    mock_run.side_effect = run_git_side_effect

    now = datetime.now(tz=timezone.utc)
    old_date = now - timedelta(days=120)
    new_date = now - timedelta(days=5)

    def date_side_effect(repo, branch):
        return old_date if branch == "old-feature" else new_date

    mock_date.side_effect = date_side_effect

    branches = detect_branches(REPO, base_branch="main", stale_days=90)
    by_name = {b.name: b for b in branches}

    assert by_name["old-feature"].is_merged is True
    assert by_name["old-feature"].is_stale is True
    assert by_name["new-feature"].is_merged is False
    assert by_name["new-feature"].is_stale is False


def test_branch_info_defaults():
    info = BranchInfo(name="test", is_merged=False)
    assert info.last_commit_date is None
    assert info.tracking_remote is None
    assert info.is_stale is False
