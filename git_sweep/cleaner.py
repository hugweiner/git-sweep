"""Branch cleanup logic for git-sweep."""

from dataclasses import dataclass
from typing import List, Optional

from git_sweep.detector import BranchInfo, _run_git


@dataclass
class CleanupResult:
    branch: str
    remote: Optional[str]
    success: bool
    error: Optional[str] = None
    dry_run: bool = False


def delete_local_branch(branch: str, force: bool = False, dry_run: bool = False) -> CleanupResult:
    """Delete a local branch. Use force=True to delete unmerged branches."""
    if dry_run:
        return CleanupResult(branch=branch, remote=None, success=True, dry_run=True)

    flag = "-D" if force else "-d"
    stdout, stderr, returncode = _run_git(["branch", flag, branch])
    if returncode != 0:
        return CleanupResult(branch=branch, remote=None, success=False, error=stderr.strip())
    return CleanupResult(branch=branch, remote=None, success=True)


def delete_remote_branch(branch: str, remote: str = "origin", dry_run: bool = False) -> CleanupResult:
    """Delete a remote tracking branch."""
    if dry_run:
        return CleanupResult(branch=branch, remote=remote, success=True, dry_run=True)

    stdout, stderr, returncode = _run_git(["push", remote, "--delete", branch])
    if returncode != 0:
        return CleanupResult(branch=branch, remote=remote, success=False, error=stderr.strip())
    return CleanupResult(branch=branch, remote=remote, success=True)


def cleanup_branches(
    branches: List[BranchInfo],
    delete_remote: bool = False,
    force: bool = False,
    dry_run: bool = False,
) -> List[CleanupResult]:
    """Clean up a list of branches, optionally including their remotes."""
    results: List[CleanupResult] = []

    for branch_info in branches:
        local_result = delete_local_branch(branch_info.name, force=force, dry_run=dry_run)
        results.append(local_result)

        if delete_remote and branch_info.remote:
            remote_result = delete_remote_branch(
                branch_info.name, remote=branch_info.remote, dry_run=dry_run
            )
            results.append(remote_result)

    return results
