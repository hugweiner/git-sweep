"""Tests for git_sweep.branch_filter."""

from __future__ import annotations

import pytest

from git_sweep.branch_filter import (
    FilterConfig,
    apply_filters,
    is_included,
    is_protected,
)
from git_sweep.detector import BranchInfo


def _branch(name: str) -> BranchInfo:
    return BranchInfo(name=name, is_merged=False, is_stale=False, last_commit_date=None)


# ---------------------------------------------------------------------------
# is_protected
# ---------------------------------------------------------------------------

def test_is_protected_default_patterns():
    cfg = FilterConfig()
    assert is_protected(_branch("main"), cfg) is True
    assert is_protected(_branch("master"), cfg) is True
    assert is_protected(_branch("develop"), cfg) is True


def test_is_protected_glob():
    cfg = FilterConfig(protect_patterns=["release/*"])
    assert is_protected(_branch("release/1.0"), cfg) is True
    assert is_protected(_branch("feature/x"), cfg) is False


def test_is_not_protected_arbitrary_branch():
    cfg = FilterConfig()
    assert is_protected(_branch("feature/cool-stuff"), cfg) is False


# ---------------------------------------------------------------------------
# is_included
# ---------------------------------------------------------------------------

def test_is_included_no_patterns_accepts_all():
    cfg = FilterConfig()
    assert is_included(_branch("feature/foo"), cfg) is True


def test_is_included_include_pattern_restricts():
    cfg = FilterConfig(include_patterns=["feature/*"])
    assert is_included(_branch("feature/foo"), cfg) is True
    assert is_included(_branch("hotfix/bar"), cfg) is False


def test_is_included_exclude_pattern_blocks():
    cfg = FilterConfig(exclude_patterns=["wip/*"])
    assert is_included(_branch("wip/draft"), cfg) is False
    assert is_included(_branch("feature/done"), cfg) is True


def test_is_included_regex_exclude():
    cfg = FilterConfig(regex_exclude=r"^temp-")
    assert is_included(_branch("temp-branch"), cfg) is False
    assert is_included(_branch("stable-branch"), cfg) is True


def test_is_included_invalid_regex_does_not_raise():
    cfg = FilterConfig(regex_exclude=r"[invalid")
    # Should not raise; invalid regex is silently ignored.
    assert is_included(_branch("any-branch"), cfg) is True


# ---------------------------------------------------------------------------
# apply_filters
# ---------------------------------------------------------------------------

def test_apply_filters_removes_protected():
    branches = [_branch("main"), _branch("feature/x"), _branch("develop")]
    cfg = FilterConfig()
    result = apply_filters(branches, cfg)
    names = [b.name for b in result]
    assert "main" not in names
    assert "develop" not in names
    assert "feature/x" in names


def test_apply_filters_empty_list():
    assert apply_filters([], FilterConfig()) == []


def test_apply_filters_combined_rules():
    branches = [
        _branch("main"),
        _branch("feature/cool"),
        _branch("wip/draft"),
        _branch("feature/done"),
    ]
    cfg = FilterConfig(
        protect_patterns=["main"],
        include_patterns=["feature/*"],
        exclude_patterns=[],
    )
    result = apply_filters(branches, cfg)
    names = [b.name for b in result]
    assert names == ["feature/cool", "feature/done"]
