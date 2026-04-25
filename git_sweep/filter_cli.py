"""CLI helpers for branch-filter configuration.

Exposes ``add_filter_args`` to attach filter-related flags to any
argparse parser, and ``filter_config_from_args`` to build a
``FilterConfig`` from parsed arguments.
"""

from __future__ import annotations

import argparse
from typing import List

from git_sweep.branch_filter import FilterConfig


def add_filter_args(parser: argparse.ArgumentParser) -> None:
    """Attach branch-filter flags to *parser* in-place."""
    parser.add_argument(
        "--include",
        metavar="PATTERN",
        dest="include_patterns",
        action="append",
        default=[],
        help="Glob pattern for branches to include (repeatable).",
    )
    parser.add_argument(
        "--exclude",
        metavar="PATTERN",
        dest="exclude_patterns",
        action="append",
        default=[],
        help="Glob pattern for branches to exclude (repeatable).",
    )
    parser.add_argument(
        "--regex-exclude",
        metavar="REGEX",
        dest="regex_exclude",
        default="",
        help="Regular expression; matching branch names are excluded.",
    )
    parser.add_argument(
        "--protect",
        metavar="PATTERN",
        dest="protect_patterns",
        action="append",
        default=[],
        help=(
            "Additional glob patterns for branches that must never be deleted "
            "(main/master/develop are always protected)."
        ),
    )


def filter_config_from_args(
    args: argparse.Namespace,
    base_protect: List[str] | None = None,
) -> FilterConfig:
    """Build a :class:`FilterConfig` from *args*.

    *base_protect* defaults to ``["main", "master", "develop"]`` and is
    extended with any ``--protect`` flags supplied on the command line.
    """
    if base_protect is None:
        base_protect = ["main", "master", "develop"]

    extra_protect: List[str] = getattr(args, "protect_patterns", []) or []
    protect = list(base_protect) + [p for p in extra_protect if p not in base_protect]

    return FilterConfig(
        protect_patterns=protect,
        include_patterns=getattr(args, "include_patterns", []) or [],
        exclude_patterns=getattr(args, "exclude_patterns", []) or [],
        regex_exclude=getattr(args, "regex_exclude", "") or "",
    )
