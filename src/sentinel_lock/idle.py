"""Idle policy and automatic-lock controller."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import logging
from threading import Event
from time import monotonic
from typing import Callable, Protocol

from sentinel_lock.activity import ActivityManager


class WorkstationLocker(Protocol):
    """Platform action used by the idle controller."""

    def lock(self) -> None:
        """Request a workstation lock or raise on failure."""


class ControllerState(str, Enum):
    ACTIVE = "active"
    LOCKED = "locked"


@dataclass(frozen=True, slots=True)
class IdleEvaluation:
    idle_seconds: float
    activity_sequence: int
    state: ControllerState
    lock_requested: bool


class IdleLockController:
    """Evaluate idle policy and request one lock per idle episode."""

    def __init__(
        self,
        activity_manager: ActivityManager,
        locker: WorkstationLocker,
        *,
        idle_timeout_seconds: float,
        poll_interval_seconds: float,
        clock: Callable[[], float] = monotonic,
        logger: logging.Logger | None = None,
    ) -> None:
        if idle_timeout_seconds <= 0:
            raise ValueError("idle_timeout_seconds must be positive")
        if poll_interval_seconds <= 0:
            raise ValueError("poll_interval_seconds must be positive")

        self._activity_manager = activity_manager
        self._locker = locker
        self._idle_timeout_seconds = idle_timeout_seconds
        self._poll_interval_seconds = poll_interval_seconds
        self._clock = clock
        self._logger = logger or logging.getLogger(__name__)
        self._observed_sequence = activity_manager.snapshot().sequence
        self._armed = True
        self._state = ControllerState.ACTIVE

    @property
    def state(self) -> ControllerState:
        return self._state

    def evaluate_once(self) -> IdleEvaluation:
        """Evaluate one policy cycle and return its observable result."""

        snapshot = self._activity_manager.snapshot()
        if snapshot.sequence != self._observed_sequence:
            self._observed_sequence = snapshot.sequence
            self._armed = True
            self._state = ControllerState.ACTIVE

        idle_seconds = snapshot.idle_seconds(self._clock())
        lock_requested = False
        if idle_seconds >= self._idle_timeout_seconds and self._armed:
            try:
                self._locker.lock()
            except Exception:
                self._logger.exception("Workstation lock request failed")
            else:
                self._armed = False
                self._state = ControllerState.LOCKED
                lock_requested = True
                self._logger.info(
                    "Workstation lock requested after %.1f idle seconds",
                    idle_seconds,
                )

        return IdleEvaluation(
            idle_seconds=idle_seconds,
            activity_sequence=snapshot.sequence,
            state=self._state,
            lock_requested=lock_requested,
        )

    def run(self, stop_event: Event) -> None:
        """Run policy evaluations until shutdown is requested."""

        while not stop_event.is_set():
            self.evaluate_once()
            stop_event.wait(self._poll_interval_seconds)
