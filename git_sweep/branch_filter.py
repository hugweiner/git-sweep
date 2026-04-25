"""Branch filtering utilities for git-sweep.

Provides composable predicates to include/exclude branches
based on glob patterns, regex, and protection rules.
"""

from __future__ import annotations

import fnmatch
import re
from dataclasses import dataclass, field
from typing import List, Sequence

from git_sweep.detector import BranchInfo


@dataclass
class FilterConfig:
    """Configuration for branch filtering."""

    protect_patterns: List[str] = field(default_factory=lambda: ["main", "master", "develop"])
    include_patterns: List[str] = field(default_factory=list)  # empty = include all
    exclude_patterns: List[str] = field(default_factory=list)
    regex_exclude: str = ""


def _matches_any(name: str, patterns: Sequence[str]) -> bool:
    """Return True if *name* matches any of the glob *patterns*."""
    return any(fnmatch.fnmatch(name, pat) for pat in patterns)


def is_protected(branch: BranchInfo, config: FilterConfig) -> bool:
    """Return True if the branch is protected and must not be deleted."""
    return _matches_any(branch.name, config.protect_patterns)


def is_included(branch: BranchInfo, config: FilterConfig) -> bool:
    """Return True if the branch passes include/exclude pattern rules."""
    name = branch.name

    # If include_patterns are specified, branch must match at least one.
    if config.include_patterns and not _matches_any(name, config.include_patterns):
        return False

    # Explicit exclude glob patterns.
    if _matches_any(name, config.exclude_patterns):
        return False

    # Optional regex exclusion.
    if config.regex_exclude:
        try:
            if re.search(config.regex_exclude, name):
                return False
        except re.error:
            pass  # Invalid regex – skip silently.

    return True


def apply_filters(
    branches: Sequence[BranchInfo],
    config: FilterConfig,
) -> List[BranchInfo]:
    """Return branches that are not protected and pass inclusion rules."""
    result = []
    for branch in branches:
        if is_protected(branch, config):
            continue
        if not is_included(branch, config):
            continue
        result.append(branch)
    return result
