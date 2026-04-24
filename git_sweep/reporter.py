"""Reporting and formatting utilities for git-sweep output."""

from typing import List

from git_sweep.cleaner import CleanupResult
from git_sweep.detector import BranchInfo


def format_branch_table(branches: List[BranchInfo]) -> str:
    """Format detected branches as a human-readable table."""
    if not branches:
        return "No branches to clean up."

    header = f"{'Branch':<40} {'Merged':<8} {'Stale':<8} {'Last Commit'}"
    separator = "-" * 75
    lines = [header, separator]

    for b in branches:
        last_commit = b.last_commit_date.strftime("%Y-%m-%d") if b.last_commit_date else "unknown"
        lines.append(f"{b.name:<40} {'yes' if b.is_merged else 'no':<8} {'yes' if b.is_stale else 'no':<8} {last_commit}")

    return "\n".join(lines)


def format_cleanup_results(results: List[CleanupResult]) -> str:
    """Format cleanup results as a summary report."""
    if not results:
        return "Nothing was cleaned up."

    success_count = sum(1 for r in results if r.success and not r.dry_run)
    dry_run_count = sum(1 for r in results if r.dry_run)
    failure_count = sum(1 for r in results if not r.success)

    lines = []
    for result in results:
        scope = f"{result.remote}/{result.branch}" if result.remote else result.branch
        if result.dry_run:
            lines.append(f"  [dry-run] would delete: {scope}")
        elif result.success:
            lines.append(f"  [deleted] {scope}")
        else:
            lines.append(f"  [failed]  {scope} — {result.error}")

    summary_parts = []
    if dry_run_count:
        summary_parts.append(f"{dry_run_count} would be deleted (dry run)")
    if success_count:
        summary_parts.append(f"{success_count} deleted")
    if failure_count:
        summary_parts.append(f"{failure_count} failed")

    lines.append("")
    lines.append("Summary: " + ", ".join(summary_parts))
    return "\n".join(lines)
