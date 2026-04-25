"""CLI sub-commands for the restore feature."""
from __future__ import annotations

import argparse
from typing import List

from git_sweep.restore import (
    load_restore_log,
    restore_branch,
    RestoreEntry,
    DEFAULT_RESTORE_FILE,
)


def build_restore_parser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    """Register 'restore' sub-commands on an existing subparser group."""
    p = subparsers.add_parser("restore", help="Restore previously deleted branches")
    sub = p.add_subparsers(dest="restore_cmd")

    # list
    sub.add_parser("list", help="List recorded deletions")

    # recover
    rec = sub.add_parser("recover", help="Recreate a deleted branch at its recorded SHA")
    rec.add_argument("branch", help="Branch name to restore")
    rec.add_argument("--dry-run", action="store_true", default=False)
    rec.add_argument("--log", default=DEFAULT_RESTORE_FILE, help="Path to restore log")


def run_restore(args: argparse.Namespace) -> int:
    """Dispatch restore sub-commands; return exit code."""
    if args.restore_cmd == "list":
        return _cmd_list(getattr(args, "log", DEFAULT_RESTORE_FILE))
    if args.restore_cmd == "recover":
        return _cmd_recover(args)
    print("No restore sub-command given. Use 'list' or 'recover'.")
    return 1


def _cmd_list(log_path: str) -> int:
    entries: List[RestoreEntry] = load_restore_log(log_path)
    if not entries:
        print("No recorded deletions.")
        return 0
    print(f"{'Branch':<35} {'SHA':<12} {'Remote':<15} Deleted At")
    print("-" * 80)
    for e in entries:
        remote = e.remote or ""
        print(f"{e.branch:<35} {e.sha:<12} {remote:<15} {e.deleted_at}")
    return 0


def _cmd_recover(args: argparse.Namespace) -> int:
    entries = load_restore_log(args.log)
    matches = [e for e in entries if e.branch == args.branch]
    if not matches:
        print(f"No restore record found for branch '{args.branch}'.")
        return 1
    entry = matches[-1]  # most recent deletion
    if args.dry_run:
        print(f"[dry-run] Would restore '{entry.branch}' at {entry.sha}")
        return 0
    ok = restore_branch(entry)
    if ok:
        print(f"Restored '{entry.branch}' at {entry.sha}.")
        return 0
    print(f"Failed to restore '{entry.branch}'.")
    return 2
