"""Scheduled sweep runner — persist and execute sweeps on a cron-like interval."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

DEFAULT_SCHEDULE_FILE = Path(".git-sweep-schedule.json")


@dataclass
class ScheduleEntry:
    interval_hours: float = 24.0
    last_run_utc: Optional[str] = None  # ISO-8601 string or None
    enabled: bool = True
    extra_args: list[str] = field(default_factory=list)

    def is_due(self, now: Optional[datetime] = None) -> bool:
        """Return True if the scheduled interval has elapsed since last run."""
        if not self.enabled:
            return False
        if self.last_run_utc is None:
            return True
        now = now or datetime.now(timezone.utc)
        last = datetime.fromisoformat(self.last_run_utc)
        elapsed_hours = (now - last).total_seconds() / 3600
        return elapsed_hours >= self.interval_hours

    def mark_ran(self, now: Optional[datetime] = None) -> None:
        """Record the current UTC time as last_run_utc."""
        now = now or datetime.now(timezone.utc)
        self.last_run_utc = now.isoformat()


def load_schedule(path: Path = DEFAULT_SCHEDULE_FILE) -> ScheduleEntry:
    """Load a ScheduleEntry from *path*, or return defaults if missing."""
    if not path.exists():
        return ScheduleEntry()
    try:
        data = json.loads(path.read_text())
        return ScheduleEntry(
            interval_hours=float(data.get("interval_hours", 24.0)),
            last_run_utc=data.get("last_run_utc"),
            enabled=bool(data.get("enabled", True)),
            extra_args=list(data.get("extra_args", [])),
        )
    except (json.JSONDecodeError, ValueError):
        return ScheduleEntry()


def save_schedule(entry: ScheduleEntry, path: Path = DEFAULT_SCHEDULE_FILE) -> None:
    """Persist *entry* to *path* as JSON."""
    path.write_text(json.dumps(asdict(entry), indent=2))


def maybe_run_sweep(
    entry: ScheduleEntry,
    run_fn,
    path: Path = DEFAULT_SCHEDULE_FILE,
    now: Optional[datetime] = None,
) -> bool:
    """Run *run_fn* if the schedule is due. Returns True if sweep was executed."""
    if not entry.is_due(now=now):
        return False
    run_fn(entry.extra_args)
    entry.mark_ran(now=now)
    save_schedule(entry, path=path)
    return True
