"""Thread-safe, privacy-preserving user activity state."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from threading import Lock
from time import monotonic
from typing import Callable


class ActivityKind(str, Enum):
    """Activity categories retained by Sentinel Lock."""

    KEYBOARD = "keyboard"
    MOUSE_MOVE = "mouse_move"
    MOUSE_CLICK = "mouse_click"


@dataclass(frozen=True, slots=True)
class ActivitySnapshot:
    """An immutable point-in-time view of activity state."""

    last_activity_monotonic: float
    last_activity_at: datetime
    last_kind: ActivityKind | None
    sequence: int

    def idle_seconds(self, now_monotonic: float) -> float:
        """Return non-negative elapsed idle time."""

        return max(0.0, now_monotonic - self.last_activity_monotonic)


class ActivityManager:
    """Serialize input activity into one minimal shared state."""

    def __init__(
        self,
        *,
        clock: Callable[[], float] = monotonic,
        wall_clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._clock = clock
        self._wall_clock = wall_clock or (lambda: datetime.now(timezone.utc))
        self._lock = Lock()
        self._last_activity_monotonic = self._clock()
        self._last_activity_at = self._wall_clock()
        self._last_kind: ActivityKind | None = None
        self._sequence = 0

    def record(self, kind: ActivityKind) -> ActivitySnapshot:
        """Record one category of activity without retaining event contents."""

        if not isinstance(kind, ActivityKind):
            raise TypeError("kind must be an ActivityKind")

        with self._lock:
            event_time = self._clock()
            observed_at = self._wall_clock()
            self._last_activity_monotonic = max(
                event_time, self._last_activity_monotonic
            )
            self._last_activity_at = observed_at
            self._last_kind = kind
            self._sequence += 1
            return self._snapshot_unlocked()

    def snapshot(self) -> ActivitySnapshot:
        """Return a consistent immutable activity snapshot."""

        with self._lock:
            return self._snapshot_unlocked()

    def idle_seconds(self) -> float:
        """Return current idle duration using the monotonic clock."""

        now = self._clock()
        with self._lock:
            return max(0.0, now - self._last_activity_monotonic)

    def _snapshot_unlocked(self) -> ActivitySnapshot:
        return ActivitySnapshot(
            last_activity_monotonic=self._last_activity_monotonic,
            last_activity_at=self._last_activity_at,
            last_kind=self._last_kind,
            sequence=self._sequence,
        )
