"""Suspend/resume discontinuity detection for the foreground runtime."""

from __future__ import annotations

from time import monotonic, time
from typing import Callable

Clock = Callable[[], float]


class ResumeDetector:
    """Treat a long polling discontinuity as a resume-like runtime gap.

    The detector intentionally does not inspect devices, sessions, or user data.
    It compares consecutive local clocks only. A long gap can be caused by system
    suspend/resume or by a heavily stalled process; treating either case as a
    resume is the safer behavior because the idle timer is re-baselined rather
    than immediately locking on stale elapsed time.
    """

    def __init__(
        self,
        *,
        gap_seconds: float = 10.0,
        monotonic_clock: Clock = monotonic,
        wall_clock: Clock = time,
    ) -> None:
        if gap_seconds <= 0:
            raise ValueError("gap_seconds must be positive")
        self._gap_seconds = gap_seconds
        self._monotonic_clock = monotonic_clock
        self._wall_clock = wall_clock
        self._last_monotonic = monotonic_clock()
        self._last_wall = wall_clock()

    def poll(self) -> bool:
        """Return True once when the interval since the prior poll is too large."""

        now_monotonic = self._monotonic_clock()
        now_wall = self._wall_clock()
        monotonic_gap = max(0.0, now_monotonic - self._last_monotonic)
        wall_gap = max(0.0, now_wall - self._last_wall)
        self._last_monotonic = now_monotonic
        self._last_wall = now_wall
        return max(monotonic_gap, wall_gap) >= self._gap_seconds
