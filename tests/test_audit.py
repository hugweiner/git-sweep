"""Tests for git_sweep.audit."""

import json
import pytest

from git_sweep.audit import (
    AuditEntry,
    load_audit,
    save_audit,
    record,
)


# ---------------------------------------------------------------------------
# AuditEntry serialisation
# ---------------------------------------------------------------------------

def test_audit_entry_to_dict_round_trip():
    entry = AuditEntry(
        timestamp="2024-01-01T00:00:00+00:00",
        action="delete_local",
        branch="feature/old",
        remote=None,
        success=True,
        error=None,
    )
    restored = AuditEntry.from_dict(entry.to_dict())
    assert restored.action == entry.action
    assert restored.branch == entry.branch
    assert restored.success is True
    assert restored.error is None


def test_audit_entry_from_dict_defaults():
    entry = AuditEntry.from_dict({})
    assert entry.timestamp == ""
    assert entry.action == ""
    assert entry.branch == ""
    assert entry.success is True


# ---------------------------------------------------------------------------
# load_audit / save_audit
# ---------------------------------------------------------------------------

def test_load_audit_returns_empty_when_no_file(tmp_path):
    result = load_audit(str(tmp_path / "missing.json"))
    assert result == []


def test_load_audit_returns_empty_on_corrupt_json(tmp_path):
    bad = tmp_path / "audit.json"
    bad.write_text("not-json", encoding="utf-8")
    result = load_audit(str(bad))
    assert result == []


def test_save_and_load_round_trip(tmp_path):
    path = str(tmp_path / "audit.json")
    entries = [
        AuditEntry(
            timestamp="2024-06-01T12:00:00+00:00",
            action="delete_remote",
            branch="bugfix/old",
            remote="origin",
            success=True,
            error=None,
        )
    ]
    save_audit(entries, path)
    loaded = load_audit(path)
    assert len(loaded) == 1
    assert loaded[0].action == "delete_remote"
    assert loaded[0].remote == "origin"


# ---------------------------------------------------------------------------
# record()
# ---------------------------------------------------------------------------

def test_record_appends_entry(tmp_path):
    path = str(tmp_path / "audit.json")
    e1 = record("delete_local", "old-branch", path=path)
    e2 = record("dry_run", "stale-branch", path=path)

    assert e1.action == "delete_local"
    assert e2.action == "dry_run"

    loaded = load_audit(path)
    assert len(loaded) == 2


def test_record_captures_failure(tmp_path):
    path = str(tmp_path / "audit.json")
    entry = record(
        "delete_remote",
        "dead-branch",
        remote="origin",
        success=False,
        error="ref not found",
        path=path,
    )
    assert entry.success is False
    assert entry.error == "ref not found"

    loaded = load_audit(path)
    assert loaded[0].error == "ref not found"


def test_record_timestamp_is_set(tmp_path):
    path = str(tmp_path / "audit.json")
    entry = record("delete_local", "branch-x", path=path)
    assert entry.timestamp != ""
    # ISO-8601 UTC marker
    assert "+00:00" in entry.timestamp
