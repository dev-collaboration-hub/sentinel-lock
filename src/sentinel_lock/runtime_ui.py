"""Optional Windows tray controls, runtime status, and local notifications."""

from __future__ import annotations

from dataclasses import dataclass
import logging
from threading import Event, Lock
from typing import Any, Callable, Protocol

from sentinel_lock.idle import ControllerState, IdleEvaluation


class LockRequester(Protocol):
    def request_lock(self) -> None:
        """Request a lock on the controller's own evaluation thread."""


@dataclass(frozen=True, slots=True)
class RuntimeSnapshot:
    state: ControllerState = ControllerState.ACTIVE
    idle_seconds: float = 0.0
    resumed_count: int = 0


class RuntimeStatus:
    """Thread-safe status exposed to the tray without private input data."""

    def __init__(self) -> None:
        self._lock = Lock()
        self._snapshot = RuntimeSnapshot()

    def observe(self, evaluation: IdleEvaluation) -> RuntimeSnapshot:
        with self._lock:
            self._snapshot = RuntimeSnapshot(
                state=evaluation.state,
                idle_seconds=evaluation.idle_seconds,
                resumed_count=self._snapshot.resumed_count,
            )
            return self._snapshot

    def note_resume(self) -> RuntimeSnapshot:
        with self._lock:
            self._snapshot = RuntimeSnapshot(
                state=ControllerState.ACTIVE,
                idle_seconds=0.0,
                resumed_count=self._snapshot.resumed_count + 1,
            )
            return self._snapshot

    def snapshot(self) -> RuntimeSnapshot:
        with self._lock:
            return self._snapshot


class TrayRuntimeExperience:
    """Native Win32 tray UI with Status, Lock now, and Exit controls."""

    def __init__(
        self,
        *,
        notifications_enabled: bool = True,
        logger: logging.Logger | None = None,
        backend_factory: Callable[..., Any] | None = None,
    ) -> None:
        self._notifications_enabled = notifications_enabled
        self._logger = logger or logging.getLogger(__name__)
        self._status = RuntimeStatus()
        self._backend_factory = backend_factory
        self._backend: Any | None = None
        self._controller: LockRequester | None = None
        self._stop_event: Event | None = None

    @property
    def status(self) -> RuntimeStatus:
        return self._status

    def start(self, controller: LockRequester, stop_event: Event) -> bool:
        """Start the stdlib-only native tray backend."""

        self._controller = controller
        self._stop_event = stop_event
        try:
            factory = self._backend_factory or self._default_backend_factory()
            backend = factory(
                status_provider=self._status_text,
                lock_now=self._lock_now,
                exit_app=self._exit,
                logger=self._logger,
            )
            backend.start()
        except Exception:
            self._logger.exception("Native system tray failed to start")
            return False
        self._backend = backend
        self._logger.info("Native system tray started")
        return True

    def observe(self, evaluation: IdleEvaluation) -> None:
        self._status.observe(evaluation)
        backend = self._backend
        if backend is None:
            return
        try:
            backend.update_tip(f"Sentinel Lock - {self._status_text()}")
            if evaluation.lock_requested:
                self._notify("Sentinel Lock", "Workstation lock requested")
        except Exception:
            self._logger.exception("System tray status update failed")

    def note_resume(self) -> None:
        self._status.note_resume()
        backend = self._backend
        if backend is None:
            return
        try:
            backend.update_tip("Sentinel Lock - Active after resume")
            self._notify("Sentinel Lock", "Idle timer reset after resume")
        except Exception:
            self._logger.exception("System tray resume update failed")

    def stop(self) -> None:
        backend = self._backend
        self._backend = None
        if backend is None:
            return
        try:
            backend.stop()
            backend.join(2.0)
        except Exception:
            self._logger.exception("System tray failed to stop")

    def _status_text(self) -> str:
        snapshot = self._status.snapshot()
        if snapshot.state is ControllerState.LOCKED:
            return "Status: lock requested"
        return f"Status: active - idle {snapshot.idle_seconds:.0f}s"

    def _lock_now(self) -> None:
        controller = self._controller
        if controller is not None:
            controller.request_lock()

    def _exit(self) -> None:
        stop_event = self._stop_event
        if stop_event is not None:
            stop_event.set()

    def _notify(self, title: str, message: str) -> None:
        backend = self._backend
        if not self._notifications_enabled or backend is None:
            return
        try:
            backend.notify(title, message)
        except Exception:
            self._logger.debug("Desktop notification is unavailable", exc_info=True)

    @staticmethod
    def _default_backend_factory() -> Callable[..., Any]:
        from sentinel_lock.win32_tray import Win32TrayBackend

        return Win32TrayBackend
