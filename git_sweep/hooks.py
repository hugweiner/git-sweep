"""Pre/post sweep hook execution — run shell scripts around cleanup."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


@dataclass
class HookConfig:
    pre_sweep: Optional[str] = None   # shell command / script path
    post_sweep: Optional[str] = None  # shell command / script path
    env: dict = field(default_factory=dict)


@dataclass
class HookResult:
    hook: str
    returncode: int
    stdout: str
    stderr: str

    @property
    def success(self) -> bool:
        return self.returncode == 0


def _run_hook(name: str, command: str, env_extra: dict) -> HookResult:
    """Execute *command* in a shell, returning a HookResult."""
    import os
    env = {**os.environ, **env_extra}
    proc = subprocess.run(
        command,
        shell=True,
        capture_output=True,
        text=True,
        env=env,
    )
    return HookResult(
        hook=name,
        returncode=proc.returncode,
        stdout=proc.stdout.strip(),
        stderr=proc.stderr.strip(),
    )


def run_pre_sweep(cfg: HookConfig) -> Optional[HookResult]:
    """Run the pre-sweep hook if configured."""
    if not cfg.pre_sweep:
        return None
    return _run_hook("pre_sweep", cfg.pre_sweep, cfg.env)


def run_post_sweep(cfg: HookConfig) -> Optional[HookResult]:
    """Run the post-sweep hook if configured."""
    if not cfg.post_sweep:
        return None
    return _run_hook("post_sweep", cfg.post_sweep, cfg.env)


def run_hooks_around(
    cfg: HookConfig,
    sweep_fn,
    abort_on_pre_failure: bool = True,
):
    """Run pre-hook, call sweep_fn(), run post-hook. Returns (pre, result, post)."""
    pre = run_pre_sweep(cfg)
    if pre is not None and not pre.success and abort_on_pre_failure:
        return pre, None, None
    result = sweep_fn()
    post = run_post_sweep(cfg)
    return pre, result, post
