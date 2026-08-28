"""Optional Windows tray controls, runtime status, and local notifications."""

from __future__ import annotations

from dataclasses import dataclass
import logging
from threading import Event, Lock
from typing import Any, Protocol

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
    """Small pystray UI with Status, Lock now, and Exit controls."""

    def __init__(
        self,
        *,
        notifications_enabled: bool = True,
        logger: logging.Logger | None = None,
    ) -> None:
        self._notifications_enabled = notifications_enabled
        self._logger = logger or logging.getLogger(__name__)
        self._status = RuntimeStatus()
        self._icon: Any | None = None
        self._controller: LockRequester | None = None
        self._stop_event: Event | None = None

    @property
    def status(self) -> RuntimeStatus:
        return self._status

    def start(self, controller: LockRequester, stop_event: Event) -> bool:
        """Start the tray UI; return False if the desktop backend is unavailable."""

        try:
            import pystray
            from PIL import Image, ImageDraw
        except ImportError:
            self._logger.warning("Tray UI dependencies are unavailable")
            return False

        self._controller = controller
        self._stop_event = stop_event
        image = Image.new("RGB", (64, 64), "white")
        draw = ImageDraw.Draw(image)
        draw.rectangle((12, 26, 52, 55), outline="black", width=5)
        draw.arc((20, 7, 44, 38), 180, 360, fill="black", width=5)

        menu = pystray.Menu(
            pystray.MenuItem(self._status_text, None, enabled=False),
            pystray.MenuItem("Lock now", self._lock_now),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Exit", self._exit),
        )
        self._icon = pystray.Icon("sentinel-lock", image, "Sentinel Lock", menu)
        try:
            self._icon.run_detached()
        except Exception:
            self._logger.exception("System tray failed to start")
            self._icon = None
            return False
        self._logger.info("System tray started")
        return True

    def observe(self, evaluation: IdleEvaluation) -> None:
        self._status.observe(evaluation)
        icon = self._icon
        if icon is not None:
            try:
                icon.title = f"Sentinel Lock - {self._status_text(None)}"
                icon.update_menu()
                if evaluation.lock_requested:
                    self._notify("Workstation lock requested", "Sentinel Lock")
            except Exception:
                self._logger.exception("System tray status update failed")

    def note_resume(self) -> None:
        self._status.note_resume()
        icon = self._icon
        if icon is not None:
            try:
                icon.title = "Sentinel Lock - Active after resume"
                icon.update_menu()
                self._notify("Idle timer reset after resume", "Sentinel Lock")
            except Exception:
                self._logger.exception("System tray resume update failed")

    def stop(self) -> None:
        icon = self._icon
        self._icon = None
        if icon is not None:
            try:
                icon.stop()
            except Exception:
                self._logger.exception("System tray failed to stop")

    def _status_text(self, _item: Any) -> str:
        snapshot = self._status.snapshot()
        if snapshot.state is ControllerState.LOCKED:
            return "Status: lock requested"
        return f"Status: active - idle {snapshot.idle_seconds:.0f}s"

    def _lock_now(self, _icon: Any, _item: Any) -> None:
        controller = self._controller
        if controller is not None:
            controller.request_lock()

    def _exit(self, icon: Any, _item: Any) -> None:
        stop_event = self._stop_event
        if stop_event is not None:
            stop_event.set()
        icon.stop()

    def _notify(self, message: str, title: str) -> None:
        if not self._notifications_enabled or self._icon is None:
            return
        try:
            self._icon.notify(message, title)
        except (AttributeError, NotImplementedError):
            self._logger.debug("Desktop notifications are unavailable")
