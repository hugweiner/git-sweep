"""Tests for git_sweep.rate_limiter."""

import time
import pytest

from git_sweep.rate_limiter import (
    RateLimitConfig,
    RateLimiter,
    get_default_limiter,
    reset_default_limiter,
)


def _fast_limiter(max_ops: int = 5, window: float = 10.0) -> RateLimiter:
    cfg = RateLimitConfig(max_operations=max_ops, window_seconds=window, min_delay_seconds=0.0)
    return RateLimiter(config=cfg)


def test_is_allowed_initially_true():
    rl = _fast_limiter(max_ops=5)
    assert rl.is_allowed() is True


def test_is_allowed_false_when_exhausted():
    rl = _fast_limiter(max_ops=3)
    for _ in range(3):
        rl.acquire()
    assert rl.is_allowed() is False


def test_remaining_decrements():
    rl = _fast_limiter(max_ops=5)
    assert rl.remaining() == 5
    rl.acquire()
    assert rl.remaining() == 4


def test_remaining_never_negative():
    rl = _fast_limiter(max_ops=2)
    rl.acquire()
    rl.acquire()
    assert rl.remaining() == 0


def test_acquire_returns_non_negative_wait():
    rl = _fast_limiter()
    wait = rl.acquire()
    assert wait >= 0.0


def test_disabled_limiter_always_allows():
    cfg = RateLimitConfig(enabled=False, max_operations=1)
    rl = RateLimiter(config=cfg)
    for _ in range(10):
        assert rl.is_allowed() is True


def test_disabled_remaining_returns_max():
    cfg = RateLimitConfig(enabled=False, max_operations=7)
    rl = RateLimiter(config=cfg)
    assert rl.remaining() == 7


def test_disabled_acquire_returns_zero():
    cfg = RateLimitConfig(enabled=False)
    rl = RateLimiter(config=cfg)
    assert rl.acquire() == 0.0


def test_eviction_restores_capacity():
    cfg = RateLimitConfig(max_operations=2, window_seconds=0.05, min_delay_seconds=0.0)
    rl = RateLimiter(config=cfg)
    rl.acquire()
    rl.acquire()
    assert rl.is_allowed() is False
    time.sleep(0.1)
    assert rl.is_allowed() is True


def test_get_default_limiter_singleton():
    reset_default_limiter()
    a = get_default_limiter()
    b = get_default_limiter()
    assert a is b


def test_reset_default_limiter_replaces_instance():
    old = get_default_limiter()
    new = reset_default_limiter()
    assert new is not old
    assert get_default_limiter() is new
