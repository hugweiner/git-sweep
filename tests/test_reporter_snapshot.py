"""Tests for snapshot-related reporter helpers."""

import pytest

from git_sweep.snapshot import BranchSnapshot, Snapshot
from git_sweep.reporter import format_snapshot_diff


def _snap(ts, names):
    return Snapshot(
        captured_at=ts,
        base_branch="main",
        branches=[BranchSnapshot(n, "2024-01-01", False, False) for n in names],
    )


def test_format_snapshot_diff_no_changes():
    old = _snap("2024-01-01T00:00:00", ["a", "b"])
    new = _snap("2024-02-01T00:00:00", ["a", "b"])
    output = format_snapshot_diff(old, new)
    assert "No changes detected" in output


def test_format_snapshot_diff_added():
    old = _snap("2024-01-01T00:00:00", ["a"])
    new = _snap("2024-02-01T00:00:00", ["a", "b", "c"])
    output = format_snapshot_diff(old, new)
    assert "+ b" in output
    assert "+ c" in output
    assert "removed" not in output.lower()


def test_format_snapshot_diff_removed():
    old = _snap("2024-01-01T00:00:00", ["a", "b", "c"])
    new = _snap("2024-02-01T00:00:00", ["a"])
    output = format_snapshot_diff(old, new)
    assert "- b" in output
    assert "- c" in output
    assert "new branches" not in output.lower()


def test_format_snapshot_diff_mixed():
    old = _snap("2024-01-01T00:00:00", ["a", "b"])
    new = _snap("2024-02-01T00:00:00", ["b", "c"])
    output = format_snapshot_diff(old, new)
    assert "+ c" in output
    assert "- a" in output


def test_format_snapshot_diff_includes_timestamps():
    old = _snap("2024-01-01T00:00:00", [])
    new = _snap("2024-06-15T08:30:00", [])
    output = format_snapshot_diff(old, new)
    assert "2024-01-01T00:00:00" in output
    assert "2024-06-15T08:30:00" in output
