"""Tests for git_sweep.snapshot."""

import json
import os
from datetime import date
from unittest.mock import MagicMock

import pytest

from git_sweep.snapshot import (
    BranchSnapshot,
    Snapshot,
    capture_snapshot,
    load_snapshot,
    save_snapshot,
)


def _make_branch(name, merged=False, stale=False):
    b = MagicMock()
    b.name = name
    b.last_commit = date(2024, 1, 15)
    b.is_merged = merged
    b.is_stale = stale
    return b


def test_capture_snapshot_basic():
    branches = [_make_branch("feat/a", merged=True), _make_branch("feat/b", stale=True)]
    snap = capture_snapshot(branches, base_branch="main")
    assert snap.base_branch == "main"
    assert len(snap.branches) == 2
    assert snap.branches[0].name == "feat/a"
    assert snap.branches[0].is_merged is True
    assert snap.branches[1].is_stale is True


def test_capture_snapshot_no_last_commit():
    b = MagicMock()
    b.name = "orphan"
    b.last_commit = None
    b.is_merged = False
    b.is_stale = False
    snap = capture_snapshot([b], base_branch="main")
    assert snap.branches[0].last_commit == ""


def test_snapshot_branch_names():
    snap = Snapshot(
        captured_at="2024-01-01T00:00:00",
        base_branch="main",
        branches=[
            BranchSnapshot("a", "2024-01-01", False, False),
            BranchSnapshot("b", "2024-01-01", True, False),
        ],
    )
    assert snap.branch_names() == ["a", "b"]


def test_snapshot_diff():
    old = Snapshot(
        captured_at="2024-01-01T00:00:00",
        base_branch="main",
        branches=[BranchSnapshot("a", "", False, False), BranchSnapshot("b", "", False, False)],
    )
    new = Snapshot(
        captured_at="2024-02-01T00:00:00",
        base_branch="main",
        branches=[BranchSnapshot("b", "", False, False), BranchSnapshot("c", "", False, False)],
    )
    diff = new.diff(old)
    assert diff["added"] == ["c"]
    assert diff["removed"] == ["a"]


def test_save_and_load_snapshot(tmp_path):
    path = str(tmp_path / "snap.json")
    snap = Snapshot(
        captured_at="2024-03-01T12:00:00",
        base_branch="develop",
        branches=[BranchSnapshot("feat/x", "2024-02-20", True, False)],
    )
    save_snapshot(snap, path)
    loaded = load_snapshot(path)
    assert loaded is not None
    assert loaded.base_branch == "develop"
    assert loaded.branches[0].name == "feat/x"
    assert loaded.branches[0].is_merged is True


def test_load_snapshot_missing_file(tmp_path):
    result = load_snapshot(str(tmp_path / "nonexistent.json"))
    assert result is None


def test_save_snapshot_creates_valid_json(tmp_path):
    path = str(tmp_path / "snap.json")
    snap = Snapshot("2024-01-01T00:00:00", "main", [])
    save_snapshot(snap, path)
    with open(path) as f:
        data = json.load(f)
    assert data["base_branch"] == "main"
    assert data["branches"] == []
