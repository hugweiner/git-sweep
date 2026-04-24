"""Tests for git_sweep.config module."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from git_sweep.config import (
    DEFAULT_BASE_BRANCHES,
    DEFAULT_STALE_DAYS,
    SweepConfig,
    load_config,
    save_config,
    _find_config,
)


def test_sweep_config_defaults():
    cfg = SweepConfig()
    assert cfg.stale_days == DEFAULT_STALE_DAYS
    assert cfg.base_branches == list(DEFAULT_BASE_BRANCHES)
    assert cfg.protected_branches == []
    assert cfg.remote == "origin"
    assert cfg.dry_run is False
    assert cfg.delete_remote is False


def test_sweep_config_round_trip():
    cfg = SweepConfig(
        base_branches=["main"],
        stale_days=30,
        protected_branches=["release"],
        remote="upstream",
        dry_run=True,
        delete_remote=True,
    )
    restored = SweepConfig.from_dict(cfg.to_dict())
    assert restored.stale_days == 30
    assert restored.base_branches == ["main"]
    assert restored.protected_branches == ["release"]
    assert restored.remote == "upstream"
    assert restored.dry_run is True
    assert restored.delete_remote is True


def test_from_dict_uses_defaults_for_missing_keys():
    cfg = SweepConfig.from_dict({})
    assert cfg.stale_days == DEFAULT_STALE_DAYS
    assert cfg.base_branches == list(DEFAULT_BASE_BRANCHES)


def test_load_config_returns_defaults_when_no_file(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    cfg = load_config()
    assert isinstance(cfg, SweepConfig)
    assert cfg.stale_days == DEFAULT_STALE_DAYS


def test_load_config_reads_file(tmp_path):
    config_file = tmp_path / ".gitsweep.json"
    config_file.write_text(json.dumps({"stale_days": 14, "remote": "upstream"}))
    cfg = load_config(str(config_file))
    assert cfg.stale_days == 14
    assert cfg.remote == "upstream"


def test_save_config_creates_file(tmp_path):
    cfg = SweepConfig(stale_days=60)
    out_path = tmp_path / "sweep.json"
    result = save_config(cfg, str(out_path))
    assert result == out_path
    data = json.loads(out_path.read_text())
    assert data["stale_days"] == 60


def test_find_config_locates_file(tmp_path, monkeypatch):
    config_file = tmp_path / ".gitsweep.json"
    config_file.write_text("{}")
    monkeypatch.chdir(tmp_path)
    found = _find_config()
    assert found == config_file


def test_find_config_returns_none_when_absent(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert _find_config() is None
