"""Tests for git_sweep.filter_cli."""

from __future__ import annotations

import argparse

import pytest

from git_sweep.filter_cli import add_filter_args, filter_config_from_args


def _parse(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    add_filter_args(parser)
    return parser.parse_args(argv)


# ---------------------------------------------------------------------------
# add_filter_args
# ---------------------------------------------------------------------------

def test_add_filter_args_registers_flags():
    parser = argparse.ArgumentParser()
    add_filter_args(parser)
    actions = {a.dest for a in parser._actions}
    assert "include_patterns" in actions
    assert "exclude_patterns" in actions
    assert "regex_exclude" in actions
    assert "protect_patterns" in actions


def test_defaults_are_empty():
    args = _parse([])
    assert args.include_patterns == []
    assert args.exclude_patterns == []
    assert args.regex_exclude == ""
    assert args.protect_patterns == []


def test_include_flag_appends():
    args = _parse(["--include", "feature/*", "--include", "hotfix/*"])
    assert args.include_patterns == ["feature/*", "hotfix/*"]


def test_exclude_flag_appends():
    args = _parse(["--exclude", "wip/*"])
    assert args.exclude_patterns == ["wip/*"]


def test_regex_exclude_flag():
    args = _parse(["--regex-exclude", r"^temp-"])
    assert args.regex_exclude == r"^temp-"


def test_protect_flag_appends():
    args = _parse(["--protect", "release/*"])
    assert args.protect_patterns == ["release/*"]


# ---------------------------------------------------------------------------
# filter_config_from_args
# ---------------------------------------------------------------------------

def test_filter_config_defaults():
    args = _parse([])
    cfg = filter_config_from_args(args)
    assert "main" in cfg.protect_patterns
    assert "master" in cfg.protect_patterns
    assert "develop" in cfg.protect_patterns
    assert cfg.include_patterns == []
    assert cfg.exclude_patterns == []
    assert cfg.regex_exclude == ""


def test_filter_config_extra_protect_merged():
    args = _parse(["--protect", "release/*"])
    cfg = filter_config_from_args(args)
    assert "release/*" in cfg.protect_patterns
    assert "main" in cfg.protect_patterns  # base still present


def test_filter_config_no_duplicate_protect():
    args = _parse(["--protect", "main"])  # main already in base
    cfg = filter_config_from_args(args)
    assert cfg.protect_patterns.count("main") == 1


def test_filter_config_custom_base_protect():
    args = _parse([])
    cfg = filter_config_from_args(args, base_protect=["trunk"])
    assert "trunk" in cfg.protect_patterns
    assert "main" not in cfg.protect_patterns


def test_filter_config_include_and_exclude():
    args = _parse(["--include", "feature/*", "--exclude", "feature/wip-*"])
    cfg = filter_config_from_args(args)
    assert cfg.include_patterns == ["feature/*"]
    assert cfg.exclude_patterns == ["feature/wip-*"]
