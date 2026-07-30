"""Mouse movement and click activity adapter."""

from __future__ import annotations

import logging
from threading import Lock
from typing import Any, Callable

from sentinel_lock.activity import ActivityKind, ActivityManager
from sentinel_lock.monitors.base import MonitorStartError

ListenerFactory = Callable[..., Any]


class MouseMonitor:
    """Route movement and pressed-click callbacks through one listener."""

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
                listener = factory(
                    on_move=self._on_move,
                    on_click=self._on_click,
                )
                listener.start()
            except Exception as exc:
                raise MonitorStartError(
                    f"mouse activity monitor failed to start: {exc}"
                ) from exc
            self._listener = listener
            self._logger.info("Mouse activity monitor started")

    def stop(self) -> None:
        with self._lifecycle_lock:
            listener = self._listener
        if listener is not None:
            try:
                listener.stop()
            except Exception:
                self._logger.exception("Mouse activity monitor failed to stop")

    def join(self, timeout: float | None = None) -> None:
        with self._lifecycle_lock:
            listener = self._listener
        if listener is not None:
            listener.join(timeout)

    def _on_move(self, _x: int, _y: int) -> None:
        try:
            self._activity_manager.record(ActivityKind.MOUSE_MOVE)
        except Exception:
            self._logger.exception("Mouse movement activity update failed")

    def _on_click(
        self,
        _x: int,
        _y: int,
        _button: object,
        pressed: bool,
    ) -> None:
        if not pressed:
            return
        try:
            self._activity_manager.record(ActivityKind.MOUSE_CLICK)
        except Exception:
            self._logger.exception("Mouse click activity update failed")

    @staticmethod
    def _default_factory() -> ListenerFactory:
        from pynput import mouse

        return mouse.Listener
