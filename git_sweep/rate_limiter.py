"""Rate limiting for git-sweep operations to avoid hammering remotes."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting."""
    max_operations: int = 30
    window_seconds: float = 60.0
    min_delay_seconds: float = 0.1
    enabled: bool = True


@dataclass
class RateLimiter:
    """Token-bucket style rate limiter for git operations."""
    config: RateLimitConfig = field(default_factory=RateLimitConfig)
    _timestamps: list = field(default_factory=list, repr=False)
    _last_call: Optional[float] = field(default=None, repr=False)

    def _evict_old(self, now: float) -> None:
        cutoff = now - self.config.window_seconds
        self._timestamps = [t for t in self._timestamps if t >= cutoff]

    def is_allowed(self) -> bool:
        """Return True if a new operation is permitted right now."""
        if not self.config.enabled:
            return True
        now = time.monotonic()
        self._evict_old(now)
        return len(self._timestamps) < self.config.max_operations

    def acquire(self) -> float:
        """Block until an operation is allowed; return the wait time in seconds."""
        if not self.config.enabled:
            return 0.0
        waited = 0.0
        while not self.is_allowed():
            time.sleep(0.05)
            waited += 0.05
        now = time.monotonic()
        if self._last_call is not None:
            gap = now - self._last_call
            if gap < self.config.min_delay_seconds:
                delay = self.config.min_delay_seconds - gap
                time.sleep(delay)
                waited += delay
                now = time.monotonic()
        self._timestamps.append(now)
        self._last_call = now
        return waited

    def remaining(self) -> int:
        """Return how many operations remain in the current window."""
        if not self.config.enabled:
            return self.config.max_operations
        now = time.monotonic()
        self._evict_old(now)
        return max(0, self.config.max_operations - len(self._timestamps))


_default_limiter: Optional[RateLimiter] = None


def get_default_limiter() -> RateLimiter:
    global _default_limiter
    if _default_limiter is None:
        _default_limiter = RateLimiter()
    return _default_limiter


def reset_default_limiter(config: Optional[RateLimitConfig] = None) -> RateLimiter:
    global _default_limiter
    _default_limiter = RateLimiter(config=config or RateLimitConfig())
    return _default_limiter
