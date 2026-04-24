"""High-level integration: wire scheduler + hooks + sweep into one callable."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, List, Optional

from git_sweep.scheduler import ScheduleEntry, load_schedule, save_schedule, maybe_run_sweep
from git_sweep.hooks import HookConfig, HookResult, run_hooks_around


@dataclass
class IntegrationResult:
    scheduled: bool
    pre_hook: Optional[HookResult]
    sweep_output: object
    post_hook: Optional[HookResult]
    aborted: bool = False

    @property
    def success(self) -> bool:
        if self.aborted:
            return False
        if self.pre_hook is not None and not self.pre_hook.success:
            return False
        if self.post_hook is not None and not self.post_hook.success:
            return False
        return True


def run_scheduled_sweep(
    sweep_fn: Callable[[List[str]], object],
    schedule_path: Path = Path(".git-sweep-schedule.json"),
    hook_cfg: Optional[HookConfig] = None,
    abort_on_pre_failure: bool = True,
    now: Optional[datetime] = None,
) -> Optional[IntegrationResult]:
    """Check the schedule; if due, run hooks + sweep and persist the updated schedule.

    Returns an IntegrationResult when the sweep ran, or None if it was skipped.
    """
    now = now or datetime.now(timezone.utc)
    entry = load_schedule(path=schedule_path)

    if not entry.is_due(now=now):
        return None

    hook_cfg = hook_cfg or HookConfig()
    result_holder: list = []

    def _sweep():
        output = sweep_fn(entry.extra_args)
        result_holder.append(output)
        return output

    pre, sweep_out, post = run_hooks_around(
        hook_cfg, _sweep, abort_on_pre_failure=abort_on_pre_failure
    )

    aborted = sweep_out is None and abort_on_pre_failure and pre is not None and not pre.success

    if not aborted:
        entry.mark_ran(now=now)
        save_schedule(entry, path=schedule_path)

    return IntegrationResult(
        scheduled=True,
        pre_hook=pre,
        sweep_output=sweep_out,
        post_hook=post,
        aborted=aborted,
    )
