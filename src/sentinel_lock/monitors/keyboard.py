"""Keyboard activity adapter."""

from __future__ import annotations

import logging
from threading import Lock
from typing import Any, Callable

from sentinel_lock.activity import ActivityKind, ActivityManager
from sentinel_lock.monitors.base import MonitorStartError

ListenerFactory = Callable[..., Any]


class KeyboardMonitor:
    """Translate key presses into privacy-preserving activity events."""

    def __init__(
        self,
        activity_manager: ActivityManager,
        *,
        listener_factory: ListenerFactory | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        self._activity_manager = activity_manager
        self._listener_factory = listener_factory
        self._logger = logger or logging.getLogger(__name__)
        self._listener: Any | None = None
        self._lifecycle_lock = Lock()

    def start(self) -> None:
        with self._lifecycle_lock:
            if self._listener is not None:
                return
            try:
                factory = self._listener_factory or self._default_factory()
                listener = factory(on_press=self._on_press)
                listener.start()
            except Exception as exc:
                raise MonitorStartError(
                    f"keyboard activity monitor failed to start: {exc}"
                ) from exc
            self._listener = listener
            self._logger.info("Keyboard activity monitor started")

    def stop(self) -> None:
        with self._lifecycle_lock:
            listener = self._listener
        if listener is not None:
            try:
                listener.stop()
            except Exception:
                self._logger.exception("Keyboard activity monitor failed to stop")

    def join(self, timeout: float | None = None) -> None:
        with self._lifecycle_lock:
            listener = self._listener
        if listener is not None:
            listener.join(timeout)

    def is_alive(self) -> bool:
        """Return listener health without exposing input content."""

        with self._lifecycle_lock:
            listener = self._listener
        if listener is None:
            return False
        probe = getattr(listener, "is_alive", None)
        if not callable(probe):
            return True
        try:
            return bool(probe())
        except Exception:
            self._logger.exception("Keyboard listener health probe failed")
            return False

    def restart(self) -> None:
        """Replace the current listener after an unexpected listener failure."""

        with self._lifecycle_lock:
            listener = self._listener
            self._listener = None
        if listener is not None:
            try:
                listener.stop()
            except Exception:
                self._logger.debug("Keyboard listener stop during restart failed", exc_info=True)
            try:
                listener.join(1.0)
            except Exception:
                self._logger.debug("Keyboard listener join during restart failed", exc_info=True)
        self.start()
        self._logger.warning("Keyboard activity monitor restarted")

    def _on_press(self, _key: object) -> None:
        try:
            self._activity_manager.record(ActivityKind.KEYBOARD)
        except Exception:
            self._logger.exception("Keyboard activity update failed")

    @staticmethod
    def _default_factory() -> ListenerFactory:
        from sentinel_lock.win32_input import Win32KeyboardListener

        return Win32KeyboardListener
