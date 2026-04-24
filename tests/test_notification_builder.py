"""Tests for git_sweep.notification_builder."""
from __future__ import annotations

from git_sweep.cleaner import CleanupResult
from git_sweep.notification_builder import build_body, build_subject
from git_sweep.snapshot import BranchSnapshot, Snapshot


def _res(branch: str, deleted: bool = True, error: str | None = None, scope: str = "local") -> CleanupResult:
    return CleanupResult(branch=branch, deleted=deleted, dry_run=False, error=error, scope=scope)


def _snap(*names: str) -> Snapshot:
    branches = [BranchSnapshot(name=n, merged=True, stale=False, last_commit=None) for n in names]
    return Snapshot(branches=branches, captured_at="2024-01-01T00:00:00")


def test_build_subject_counts_deleted():
    results = [_res("feat/a"), _res("feat/b"), _res("feat/c", deleted=False, error="oops")]
    subject = build_subject(results, repo="myrepo")
    assert "2" in subject
    assert "myrepo" in subject


def test_build_subject_zero_deleted():
    results = [_res("feat/a", deleted=False)]
    subject = build_subject(results, repo="proj")
    assert "0" in subject


def test_build_body_contains_deleted_section():
    results = [_res("feat/login"), _res("fix/typo")]
    body = build_body(results)
    assert "Deleted" in body
    assert "feat/login" in body
    assert "fix/typo" in body


def test_build_body_contains_failed_section():
    results = [_res("feat/broken", deleted=False, error="permission denied")]
    body = build_body(results)
    assert "Failed" in body
    assert "permission denied" in body


def test_build_body_contains_skipped_section():
    results = [_res("feat/keep", deleted=False, error=None)]
    body = build_body(results)
    assert "Skipped" in body
    assert "feat/keep" in body


def test_build_body_dry_run_label():
    results = [_res("feat/x")]
    body = build_body(results, dry_run=True)
    assert "DRY RUN" in body


def test_build_body_snapshot_delta():
    before = _snap("feat/a", "feat/b", "main")
    after = _snap("main")
    results = [_res("feat/a"), _res("feat/b")]
    body = build_body(results, before=before, after=after)
    assert "feat/a" in body
    assert "feat/b" in body
    assert "Snapshot delta" in body


def test_build_body_no_snapshot_omits_delta():
    results = [_res("feat/z")]
    body = build_body(results)
    assert "Snapshot delta" not in body
