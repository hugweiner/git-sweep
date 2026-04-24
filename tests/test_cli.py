"""Tests for git_sweep.cli module."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from git_sweep.cli import build_parser, merge_cli_into_config, run
from git_sweep.config import SweepConfig


def test_build_parser_returns_parser():
    parser = build_parser()
    assert parser.prog == "git-sweep"


def test_merge_cli_overrides_base():
    cfg = SweepConfig()
    args = build_parser().parse_args(["--base", "trunk"])
    result = merge_cli_into_config(cfg, args)
    assert result.base_branches == ["trunk"]


def test_merge_cli_dry_run():
    cfg = SweepConfig()
    args = build_parser().parse_args(["--dry-run"])
    result = merge_cli_into_config(cfg, args)
    assert result.dry_run is True


def test_merge_cli_stale_days():
    cfg = SweepConfig()
    args = build_parser().parse_args(["--stale-days", "14"])
    result = merge_cli_into_config(cfg, args)
    assert result.stale_days == 14


def test_merge_cli_protect_merges_with_existing():
    cfg = SweepConfig(protected_branches=["release"])
    args = build_parser().parse_args(["--protect", "hotfix"])
    result = merge_cli_into_config(cfg, args)
    assert "release" in result.protected_branches
    assert "hotfix" in result.protected_branches


def test_run_init_writes_config(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    cfg_file = str(tmp_path / "sweep.json")
    exit_code = run(["--init", "--config", cfg_file])
    assert exit_code == 0
    assert Path(cfg_file).exists()


def test_run_no_candidates_exits_zero(monkeypatch):
    monkeypatch.setattr("git_sweep.cli.detect_branches", lambda **_: [])
    monkeypatch.setattr("git_sweep.cli.load_config", lambda _: SweepConfig())
    exit_code = run([])
    assert exit_code == 0


def test_run_with_candidates_calls_cleanup(monkeypatch):
    from git_sweep.detector import BranchInfo
    from datetime import datetime

    branch = BranchInfo(name="old-feature", is_merged=True, is_stale=True, last_commit=datetime(2022, 1, 1))
    monkeypatch.setattr("git_sweep.cli.detect_branches", lambda **_: [branch])
    monkeypatch.setattr("git_sweep.cli.load_config", lambda _: SweepConfig(dry_run=True))
    mock_cleanup = MagicMock(return_value=[])
    monkeypatch.setattr("git_sweep.cli.cleanup_branches", mock_cleanup)
    run([])
    mock_cleanup.assert_called_once()
