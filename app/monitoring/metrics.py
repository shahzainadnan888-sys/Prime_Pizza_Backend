"""In-process metrics registry for production monitoring hooks."""

from __future__ import annotations

import time
from collections import defaultdict
from dataclasses import dataclass, field
from threading import Lock
from typing import Any


@dataclass
class _Counter:
    value: int = 0


@dataclass
class _TimerStats:
    count: int = 0
    total_ms: float = 0.0
    max_ms: float = 0.0

    def observe(self, duration_ms: float) -> None:
        self.count += 1
        self.total_ms += duration_ms
        if duration_ms > self.max_ms:
            self.max_ms = duration_ms

    @property
    def avg_ms(self) -> float:
        if self.count == 0:
            return 0.0
        return round(self.total_ms / self.count, 3)


@dataclass
class MetricsRegistry:
    """
    Lightweight process-local metrics.

    Designed to be scraped by a future Prometheus exporter or read via
    /health/services without requiring an external metrics stack at boot.
    """

    _lock: Lock = field(default_factory=Lock, repr=False)
    _counters: dict[str, _Counter] = field(default_factory=lambda: defaultdict(_Counter))
    _timers: dict[str, _TimerStats] = field(default_factory=lambda: defaultdict(_TimerStats))
    started_at: float = field(default_factory=time.time)

    def incr(self, name: str, *, amount: int = 1) -> None:
        with self._lock:
            self._counters[name].value += amount

    def observe(self, name: str, duration_ms: float) -> None:
        with self._lock:
            self._timers[name].observe(duration_ms)

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            return {
                "uptime_seconds": round(time.time() - self.started_at, 2),
                "counters": {k: v.value for k, v in self._counters.items()},
                "timers": {
                    k: {
                        "count": v.count,
                        "avg_ms": v.avg_ms,
                        "max_ms": round(v.max_ms, 3),
                        "total_ms": round(v.total_ms, 3),
                    }
                    for k, v in self._timers.items()
                },
            }


metrics = MetricsRegistry()
