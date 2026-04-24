"""Tests for git_sweep.hooks."""

from __future__ import annotations

from unittest.mock import patch, MagicMock

import pytest

from git_sweep.hooks import (
    HookConfig,
    HookResult,
    run_pre_sweep,
    run_post_sweep,
    run_hooks_around,
)


def _make_proc(returncode=0, stdout="ok", stderr=""):
    m = MagicMock()
    m.returncode = returncode
    m.stdout = stdout
    m.stderr = stderr
    return m


def test_run_pre_sweep_none_when_no_command():
    cfg = HookConfig()
    assert run_pre_sweep(cfg) is None


def test_run_post_sweep_none_when_no_command():
    cfg = HookConfig()
    assert run_post_sweep(cfg) is None


def test_run_pre_sweep_success():
    cfg = HookConfig(pre_sweep="echo hello")
    with patch("subprocess.run", return_value=_make_proc(0, "hello")) as mock_run:
        result = run_pre_sweep(cfg)
    assert result is not None
    assert result.success is True
    assert result.hook == "pre_sweep"
    assert result.stdout == "hello"


def test_run_post_sweep_failure():
    cfg = HookConfig(post_sweep="exit 1")
    with patch("subprocess.run", return_value=_make_proc(1, "", "error")):
        result = run_post_sweep(cfg)
    assert result is not None
    assert result.success is False
    assert result.returncode == 1


def test_run_hooks_around_full_flow():
    cfg = HookConfig(pre_sweep="echo pre", post_sweep="echo post")
    sweep_calls = []

    def sweep():
        sweep_calls.append(True)
        return "sweep_result"

    with patch("subprocess.run", return_value=_make_proc(0, "ok")):
        pre, result, post = run_hooks_around(cfg, sweep)

    assert pre.success is True
    assert result == "sweep_result"
    assert post.success is True
    assert len(sweep_calls) == 1


def test_run_hooks_around_aborts_on_pre_failure():
    cfg = HookConfig(pre_sweep="bad_cmd")
    sweep_calls = []

    with patch("subprocess.run", return_value=_make_proc(1, "", "fail")):
        pre, result, post = run_hooks_around(cfg, lambda: sweep_calls.append(1), abort_on_pre_failure=True)

    assert pre.success is False
    assert result is None
    assert post is None
    assert sweep_calls == []


def test_run_hooks_around_continues_on_pre_failure_if_not_aborting():
    cfg = HookConfig(pre_sweep="bad_cmd")
    sweep_calls = []

    with patch("subprocess.run", return_value=_make_proc(1)):
        pre, result, post = run_hooks_around(
            cfg, lambda: sweep_calls.append("ran") or "ok", abort_on_pre_failure=False
        )

    assert result == "ok"
    assert sweep_calls == ["ran"]
