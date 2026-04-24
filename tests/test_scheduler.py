"""Tests for git_sweep.scheduler."""

from __future__ import annotations

import json
from datetime import datetime, timezone, timedelta
from pathlib import Path

import pytest

from git_sweep.scheduler import (
    ScheduleEntry,
    load_schedule,
    save_schedule,
    maybe_run_sweep,
)


NOW = datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc)
OLD = NOW - timedelta(hours=25)
RECENT = NOW - timedelta(hours=1)


def test_is_due_when_never_run():
    entry = ScheduleEntry(interval_hours=24.0, last_run_utc=None)
    assert entry.is_due(now=NOW) is True


def test_is_due_when_interval_elapsed():
    entry = ScheduleEntry(interval_hours=24.0, last_run_utc=OLD.isoformat())
    assert entry.is_due(now=NOW) is True


def test_not_due_when_recent():
    entry = ScheduleEntry(interval_hours=24.0, last_run_utc=RECENT.isoformat())
    assert entry.is_due(now=NOW) is False


def test_not_due_when_disabled():
    entry = ScheduleEntry(enabled=False, last_run_utc=None)
    assert entry.is_due(now=NOW) is False


def test_mark_ran_updates_timestamp():
    entry = ScheduleEntry()
    entry.mark_ran(now=NOW)
    assert entry.last_run_utc == NOW.isoformat()


def test_save_and_load_roundtrip(tmp_path):
    path = tmp_path / "schedule.json"
    entry = ScheduleEntry(interval_hours=12.0, last_run_utc=NOW.isoformat(), extra_args=["--dry-run"])
    save_schedule(entry, path=path)
    loaded = load_schedule(path=path)
    assert loaded.interval_hours == 12.0
    assert loaded.last_run_utc == NOW.isoformat()
    assert loaded.extra_args == ["--dry-run"]


def test_load_schedule_missing_file(tmp_path):
    entry = load_schedule(path=tmp_path / "nonexistent.json")
    assert entry.interval_hours == 24.0
    assert entry.last_run_utc is None


def test_load_schedule_corrupt_file(tmp_path):
    path = tmp_path / "bad.json"
    path.write_text("not json{{")
    entry = load_schedule(path=path)
    assert entry.interval_hours == 24.0


def test_maybe_run_sweep_executes_when_due(tmp_path):
    path = tmp_path / "schedule.json"
    entry = ScheduleEntry(interval_hours=24.0)
    calls = []
    ran = maybe_run_sweep(entry, lambda args: calls.append(args), path=path, now=NOW)
    assert ran is True
    assert len(calls) == 1
    assert entry.last_run_utc == NOW.isoformat()


def test_maybe_run_sweep_skips_when_not_due(tmp_path):
    path = tmp_path / "schedule.json"
    entry = ScheduleEntry(interval_hours=24.0, last_run_utc=RECENT.isoformat())
    calls = []
    ran = maybe_run_sweep(entry, lambda args: calls.append(args), path=path, now=NOW)
    assert ran is False
    assert calls == []
