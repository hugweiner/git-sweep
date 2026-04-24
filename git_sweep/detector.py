"""Detect merged and stale branches in a git repository."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import List, Optional


@dataclass
class BranchInfo:
    name: str
    is_merged: bool
    last_commit_date: Optional[datetime] = None
    tracking_remote: Optional[str] = None
    is_stale: bool = False


def _run_git(args: List[str], cwd: str) -> str:
    result = subprocess.run(
        ["git"] + args,
        cwd=cwd,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def get_merged_branches(repo_path: str, base_branch: str = "main") -> List[str]:
    """Return local branches fully merged into *base_branch*."""
    output = _run_git(
        ["branch", "--merged", base_branch, "--format=%(refname:short)"],
        cwd=repo_path,
    )
    excluded = {base_branch, "master", "HEAD"}
    return [b for b in output.splitlines() if b and b not in excluded]


def get_branch_last_commit_date(repo_path: str, branch: str) -> Optional[datetime]:
    """Return the UTC datetime of the most recent commit on *branch*."""
    try:
        ts = _run_git(
            ["log", "-1", "--format=%ct", branch],
            cwd=repo_path,
        )
        if ts:
            return datetime.fromtimestamp(int(ts), tz=timezone.utc)
    except subprocess.CalledProcessError:
        pass
    return None


def detect_branches(
    repo_path: str,
    base_branch: str = "main",
    stale_days: int = 90,
) -> List[BranchInfo]:
    """Analyse local branches and return a list of :class:`BranchInfo` objects.

    A branch is considered *stale* when its last commit is older than
    *stale_days* days, regardless of merge status.
    """
    merged = set(get_merged_branches(repo_path, base_branch))
    all_branches_raw = _run_git(
        ["branch", "--format=%(refname:short)"],
        cwd=repo_path,
    )
    all_branches = [
        b for b in all_branches_raw.splitlines()
        if b and b not in {base_branch, "master", "HEAD"}
    ]

    cutoff = datetime.now(tz=timezone.utc) - timedelta(days=stale_days)
    results: List[BranchInfo] = []

    for branch in all_branches:
        last_commit = get_branch_last_commit_date(repo_path, branch)
        is_stale = bool(last_commit and last_commit < cutoff)
        results.append(
            BranchInfo(
                name=branch,
                is_merged=branch in merged,
                last_commit_date=last_commit,
                is_stale=is_stale,
            )
        )

    return results
