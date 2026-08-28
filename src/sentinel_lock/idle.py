"""Idle tracking and automatic-lock controller."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import logging
from threading import Event
from time import monotonic
from typing import Callable, Protocol

from sentinel_lock.activity import ActivityManager


class WorkstationLocker(Protocol):
    """Platform action used by the lock controller."""

    def lock(self) -> None:
        """Request a workstation lock or raise on failure."""


class ResumePoller(Protocol):
    def poll(self) -> bool:
        """Return whether a resume-like runtime gap was observed."""


class ControllerState(str, Enum):
    ACTIVE = "active"
    LOCKED = "locked"


@dataclass(frozen=True, slots=True)
class IdleEvaluation:
    idle_seconds: float
    activity_sequence: int
    state: ControllerState
    lock_requested: bool


def should_lock(idle_seconds: float, idle_timeout_seconds: float) -> bool:
    """Return whether keyboard/mouse inactivity requires a workstation lock."""

    return idle_seconds >= idle_timeout_seconds


class IdleLockController:
    """Request at most one workstation lock per keyboard/mouse idle episode."""

    def __init__(
        self,
        activity_manager: ActivityManager,
        locker: WorkstationLocker,
        *,
        idle_timeout_seconds: float,
        poll_interval_seconds: float,
        clock: Callable[[], float] = monotonic,
        logger: logging.Logger | None = None,
        resume_detector: ResumePoller | None = None,
        evaluation_observer: Callable[[IdleEvaluation], None] | None = None,
        resume_observer: Callable[[], None] | None = None,
        maintenance_callback: Callable[[], object] | None = None,
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
        self._resume_detector = resume_detector
        self._evaluation_observer = evaluation_observer
        self._resume_observer = resume_observer
        self._maintenance_callback = maintenance_callback
        self._observed_sequence = activity_manager.snapshot().sequence
        self._armed = True
        self._state = ControllerState.ACTIVE
        self._resume_baseline: float | None = None
        self._force_lock = Event()

    @property
    def state(self) -> ControllerState:
        return self._state

    def request_lock(self) -> None:
        """Queue a user-requested lock for the controller thread."""

        self._force_lock.set()

    def handle_resume(self) -> None:
        """Re-baseline idle time after a suspend/resume-like discontinuity."""

        self._resume_baseline = self._clock()
        self._armed = True
        self._state = ControllerState.ACTIVE
        self._force_lock.clear()
        self._logger.info("Runtime resume detected; idle timer re-baselined")

    def evaluate_once(self) -> IdleEvaluation:
        """Evaluate one lock cycle and return its observable result."""

        snapshot = self._activity_manager.snapshot()
        if snapshot.sequence != self._observed_sequence:
            self._observed_sequence = snapshot.sequence
            self._armed = True
            self._state = ControllerState.ACTIVE
            self._resume_baseline = None

        now = self._clock()
        idle_seconds = snapshot.idle_seconds(now)
        if self._resume_baseline is not None:
            idle_seconds = min(idle_seconds, max(0.0, now - self._resume_baseline))

        forced = self._force_lock.is_set()
        if forced:
            self._force_lock.clear()

        lock_requested = False
        if self._armed and (forced or should_lock(idle_seconds, self._idle_timeout_seconds)):
            try:
                self._locker.lock()
            except Exception:
                self._logger.exception("Workstation lock request failed")
            else:
                self._armed = False
                self._state = ControllerState.LOCKED
                lock_requested = True
                if forced:
                    self._logger.info("Workstation lock requested by runtime control")
                else:
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
        """Run lock evaluations until shutdown is requested."""

        while not stop_event.is_set():
            self._call_maintenance_callback()

            if self._resume_detector is not None:
                try:
                    resumed = self._resume_detector.poll()
                except Exception:
                    self._logger.exception("Resume detector failed")
                    resumed = False
                if resumed:
                    self.handle_resume()
                    self._call_resume_observer()

            evaluation = self.evaluate_once()
            self._call_evaluation_observer(evaluation)
            stop_event.wait(self._poll_interval_seconds)

    def _call_maintenance_callback(self) -> None:
        if self._maintenance_callback is None:
            return
        try:
            self._maintenance_callback()
        except Exception:
            self._logger.exception("Runtime maintenance callback failed")

    def _call_evaluation_observer(self, evaluation: IdleEvaluation) -> None:
        if self._evaluation_observer is None:
            return
        try:
            self._evaluation_observer(evaluation)
        except Exception:
            self._logger.exception("Runtime status observer failed")

    def _call_resume_observer(self) -> None:
        if self._resume_observer is None:
            return
        try:
            self._resume_observer()
        except Exception:
            self._logger.exception("Runtime resume observer failed")
