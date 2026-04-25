"""Tests for git_sweep.restore."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from git_sweep.restore import (
    RestoreEntry,
    load_restore_log,
    save_restore_log,
    record_deletion,
    restore_branch,
    DEFAULT_RESTORE_FILE,
)


def test_restore_entry_round_trip():
    entry = RestoreEntry(branch="feat/x", sha="abc123", remote="origin", deleted_at="2024-01-01T00:00:00")
    assert RestoreEntry.from_dict(entry.to_dict()) == entry


def test_restore_entry_from_dict_defaults():
    entry = RestoreEntry.from_dict({})
    assert entry.branch == ""
    assert entry.sha == ""
    assert entry.remote is None
    assert entry.deleted_at == ""


def test_load_restore_log_missing_file(tmp_path):
    result = load_restore_log(str(tmp_path / "nope.json"))
    assert result == []


def test_load_restore_log_corrupt_json(tmp_path):
    f = tmp_path / "restore.json"
    f.write_text("not-json")
    result = load_restore_log(str(f))
    assert result == []


def test_save_and_load_round_trip(tmp_path):
    path = str(tmp_path / "restore.json")
    entries = [
        RestoreEntry(branch="main", sha="aaa", deleted_at="2024-01-01T00:00:00"),
        RestoreEntry(branch="dev", sha="bbb", remote="origin", deleted_at="2024-01-02T00:00:00"),
    ]
    save_restore_log(entries, path)
    loaded = load_restore_log(path)
    assert len(loaded) == 2
    assert loaded[0].branch == "main"
    assert loaded[1].remote == "origin"


def test_record_deletion_appends(tmp_path):
    path = str(tmp_path / "restore.json")
    record_deletion("feat/a", "sha1", "2024-01-01T00:00:00", path=path)
    record_deletion("feat/b", "sha2", "2024-01-02T00:00:00", remote="origin", path=path)
    entries = load_restore_log(path)
    assert len(entries) == 2
    assert entries[1].branch == "feat/b"
    assert entries[1].remote == "origin"


def test_restore_branch_dry_run():
    entry = RestoreEntry(branch="feat/x", sha="abc123", deleted_at="2024-01-01T00:00:00")
    assert restore_branch(entry, dry_run=True) is True


def test_restore_branch_success():
    entry = RestoreEntry(branch="feat/x", sha="abc123", deleted_at="2024-01-01T00:00:00")
    mock_proc = MagicMock(returncode=0)
    with patch("subprocess.run", return_value=mock_proc) as mock_run:
        result = restore_branch(entry)
    assert result is True
    mock_run.assert_called_once_with(
        ["git", "branch", "feat/x", "abc123"],
        capture_output=True,
        text=True,
    )


def test_restore_branch_failure():
    entry = RestoreEntry(branch="feat/x", sha="abc123", deleted_at="2024-01-01T00:00:00")
    mock_proc = MagicMock(returncode=1)
    with patch("subprocess.run", return_value=mock_proc):
        result = restore_branch(entry)
    assert result is False
