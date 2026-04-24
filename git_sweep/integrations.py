"""Integrations: tie together sweep pipeline with scheduling, hooks, and snapshots."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from git_sweep.config import SweepConfig, load_config
from git_sweep.detector import detect_branches
from git_sweep.cleaner import cleanup_branches
from git_sweep.hooks import run_pre_sweep, run_post_sweep
from git_sweep.scheduler import is_due, mark_ran, load_schedule, save_schedule
from git_sweep.snapshot import capture_snapshot, load_snapshot, save_snapshot
from git_sweep.reporter import format_snapshot_diff


@dataclass
class IntegrationResult:
    ran: bool
    skipped_reason: Optional[str]
    branches_cleaned: int
    snapshot_diff: Optional[str]
    error: Optional[str]


def success(cleaned: int, diff: Optional[str] = None) -> IntegrationResult:
    return IntegrationResult(
        ran=True,
        skipped_reason=None,
        branches_cleaned=cleaned,
        snapshot_diff=diff,
        error=None,
    )


def run_scheduled_sweep(
    config_path: Optional[str] = None,
    schedule_path: Optional[str] = None,
    snapshot_path: Optional[str] = None,
) -> IntegrationResult:
    cfg = load_config(config_path) if config_path else load_config()
    schedule = load_schedule(schedule_path) if schedule_path else load_schedule()

    if not is_due(schedule):
        return IntegrationResult(
            ran=False,
            skipped_reason="not due",
            branches_cleaned=0,
            snapshot_diff=None,
            error=None,
        )

    result = _sweep(cfg, snapshot_path=snapshot_path)

    if result.ran:
        mark_ran(schedule)
        if schedule_path:
            save_schedule(schedule, schedule_path)
        else:
            save_schedule(schedule)

    return result


def _sweep(
    cfg: SweepConfig,
    snapshot_path: Optional[str] = None,
) -> IntegrationResult:
    pre = run_pre_sweep(cfg)
    if pre is not None and not pre.success:
        return IntegrationResult(
            ran=False,
            skipped_reason="pre-sweep hook failed",
            branches_cleaned=0,
            snapshot_diff=None,
            error=pre.output,
        )

    try:
        branches = detect_branches(cfg)
    except Exception as exc:  # noqa: BLE001
        return IntegrationResult(ran=False, skipped_reason=None, branches_cleaned=0, snapshot_diff=None, error=str(exc))

    old_snap = load_snapshot(snapshot_path) if snapshot_path else load_snapshot()
    new_snap = capture_snapshot(branches, base_branch=cfg.base_branch)

    diff_str: Optional[str] = None
    if old_snap is not None:
        diff_str = format_snapshot_diff(old_snap, new_snap)

    if snapshot_path:
        save_snapshot(new_snap, snapshot_path)
    else:
        save_snapshot(new_snap)

    results = cleanup_branches(branches, cfg)
    cleaned = sum(1 for r in results if r.success and not r.dry_run)

    run_post_sweep(cfg)

    return success(cleaned, diff_str)
