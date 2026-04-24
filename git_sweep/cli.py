"""Command-line interface for git-sweep."""

from __future__ import annotations

import argparse
import sys
from typing import List, Optional

from git_sweep.config import SweepConfig, load_config, save_config
from git_sweep.detector import detect_branches
from git_sweep.cleaner import cleanup_branches
from git_sweep.reporter import format_branch_table, format_cleanup_results


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="git-sweep",
        description="Automatically clean up merged and stale git branches.",
    )
    parser.add_argument("--config", metavar="FILE", help="Path to .gitsweep.json config file")
    parser.add_argument("--base", nargs="+", metavar="BRANCH", help="Base branches to compare against")
    parser.add_argument("--stale-days", type=int, metavar="N", help="Days of inactivity before a branch is stale")
    parser.add_argument("--remote", metavar="NAME", help="Remote name (default: origin)")
    parser.add_argument("--protect", nargs="+", metavar="BRANCH", help="Additional branches to protect")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be deleted without deleting")
    parser.add_argument("--delete-remote", action="store_true", help="Also delete remote tracking branches")
    parser.add_argument("--init", action="store_true", help="Write a default config file and exit")
    return parser


def merge_cli_into_config(config: SweepConfig, args: argparse.Namespace) -> SweepConfig:
    """Override config fields with explicit CLI arguments."""
    if args.base:
        config.base_branches = args.base
    if args.stale_days is not None:
        config.stale_days = args.stale_days
    if args.remote:
        config.remote = args.remote
    if args.protect:
        config.protected_branches = list(set(config.protected_branches) | set(args.protect))
    if args.dry_run:
        config.dry_run = True
    if args.delete_remote:
        config.delete_remote = True
    return config


def run(argv: Optional[List[str]] = None) -> int:
    """Entry point; returns exit code."""
    parser = build_parser()
    args = parser.parse_args(argv)

    config = load_config(args.config)
    config = merge_cli_into_config(config, args)

    if args.init:
        path = save_config(config, args.config)
        print(f"Config written to {path}")
        return 0

    branches = detect_branches(
        base_branches=config.base_branches,
        stale_days=config.stale_days,
        remote=config.remote,
    )

    protected = set(config.base_branches) | set(config.protected_branches)
    candidates = [b for b in branches if b.name not in protected]

    print(format_branch_table(candidates))

    if not candidates:
        print("Nothing to clean up.")
        return 0

    results = cleanup_branches(
        branches=candidates,
        dry_run=config.dry_run,
        delete_remote=config.delete_remote,
        remote=config.remote,
    )

    print(format_cleanup_results(results))
    return 0


def main() -> None:
    sys.exit(run())


if __name__ == "__main__":
    main()
