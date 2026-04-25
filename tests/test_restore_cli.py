"""Tests for git_sweep.restore_cli."""
from __future__ import annotations

import argparse
from unittest.mock import patch

import pytest

from git_sweep.restore import RestoreEntry, save_restore_log
from git_sweep.restore_cli import build_restore_parser, run_restore


def _make_args(**kwargs) -> argparse.Namespace:
    defaults = {"restore_cmd": None, "branch": None, "dry_run": False, "log": ".git-sweep-restore.json"}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_build_restore_parser_registers_subcommands():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd")
    build_restore_parser(sub)
    ns = parser.parse_args(["restore", "list"])
    assert ns.restore_cmd == "list"


def test_run_restore_no_subcommand(capsys):
    args = _make_args(restore_cmd=None)
    code = run_restore(args)
    assert code == 1
    out = capsys.readouterr().out
    assert "No restore sub-command" in out


def test_cmd_list_empty(tmp_path, capsys):
    log = str(tmp_path / "r.json")
    args = _make_args(restore_cmd="list", log=log)
    code = run_restore(args)
    assert code == 0
    assert "No recorded deletions" in capsys.readouterr().out


def test_cmd_list_with_entries(tmp_path, capsys):
    log = str(tmp_path / "r.json")
    entries = [
        RestoreEntry(branch="feat/a", sha="abc1234", deleted_at="2024-01-01T00:00:00"),
        RestoreEntry(branch="feat/b", sha="def5678", remote="origin", deleted_at="2024-01-02T00:00:00"),
    ]
    save_restore_log(entries, log)
    args = _make_args(restore_cmd="list", log=log)
    code = run_restore(args)
    assert code == 0
    out = capsys.readouterr().out
    assert "feat/a" in out
    assert "feat/b" in out
    assert "origin" in out


def test_cmd_recover_not_found(tmp_path, capsys):
    log = str(tmp_path / "r.json")
    args = _make_args(restore_cmd="recover", branch="missing", dry_run=False, log=log)
    code = run_restore(args)
    assert code == 1
    assert "No restore record" in capsys.readouterr().out


def test_cmd_recover_dry_run(tmp_path, capsys):
    log = str(tmp_path / "r.json")
    save_restore_log([RestoreEntry(branch="feat/x", sha="aaa111", deleted_at="2024-01-01T00:00:00")], log)
    args = _make_args(restore_cmd="recover", branch="feat/x", dry_run=True, log=log)
    code = run_restore(args)
    assert code == 0
    assert "dry-run" in capsys.readouterr().out


def test_cmd_recover_success(tmp_path, capsys):
    log = str(tmp_path / "r.json")
    save_restore_log([RestoreEntry(branch="feat/x", sha="aaa111", deleted_at="2024-01-01T00:00:00")], log)
    args = _make_args(restore_cmd="recover", branch="feat/x", dry_run=False, log=log)
    with patch("git_sweep.restore_cli.restore_branch", return_value=True):
        code = run_restore(args)
    assert code == 0
    assert "Restored" in capsys.readouterr().out


def test_cmd_recover_failure(tmp_path, capsys):
    log = str(tmp_path / "r.json")
    save_restore_log([RestoreEntry(branch="feat/x", sha="aaa111", deleted_at="2024-01-01T00:00:00")], log)
    args = _make_args(restore_cmd="recover", branch="feat/x", dry_run=False, log=log)
    with patch("git_sweep.restore_cli.restore_branch", return_value=False):
        code = run_restore(args)
    assert code == 2
    assert "Failed" in capsys.readouterr().out
