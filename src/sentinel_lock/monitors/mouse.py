"""Mouse movement and click activity adapter."""

from __future__ import annotations

import logging
from threading import Lock
from time import monotonic
from typing import Any, Callable

from sentinel_lock.activity import ActivityKind, ActivityManager
from sentinel_lock.monitors.base import MonitorStartError

ListenerFactory = Callable[..., Any]
Clock = Callable[[], float]

MOVEMENT_CONFIRMATION_WINDOW_SECONDS = 0.25
MOVEMENT_REFRESH_INTERVAL_SECONDS = 0.50


class _MouseMovementFilter:
    """Confirm movement bursts using timing only, never pointer coordinates."""

    def __init__(self, clock: Clock) -> None:
        self._clock = clock
        self._last_move_at: float | None = None
        self._last_refresh_at: float | None = None
        self._lock = Lock()

    def reset(self) -> None:
        with self._lock:
            self._last_move_at = None
            self._last_refresh_at = None

    def accepts_move(self) -> bool:
        now = self._clock()
        with self._lock:
            previous_move_at = self._last_move_at
            self._last_move_at = now

            if previous_move_at is None:
                return False

            move_gap = now - previous_move_at
            if move_gap < 0 or move_gap > MOVEMENT_CONFIRMATION_WINDOW_SECONDS:
                return False

            if self._last_refresh_at is not None:
                refresh_gap = now - self._last_refresh_at
                if refresh_gap < 0:
                    self._last_refresh_at = None
                elif refresh_gap < MOVEMENT_REFRESH_INTERVAL_SECONDS:
                    return False

            self._last_refresh_at = now
            return True


class MouseMonitor:
    """Route filtered movement and pressed-click callbacks through one listener."""

    def __init__(
        self,
        activity_manager: ActivityManager,
        *,
        listener_factory: ListenerFactory | None = None,
        logger: logging.Logger | None = None,
        clock: Clock = monotonic,
    ) -> None:
        self._activity_manager = activity_manager
        self._listener_factory = listener_factory
        self._logger = logger or logging.getLogger(__name__)
        self._listener: Any | None = None
        self._lifecycle_lock = Lock()
        self._movement_filter = _MouseMovementFilter(clock)

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

    def is_alive(self) -> bool:
        """Return listener health without retaining pointer information."""

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
            self._logger.exception("Mouse listener health probe failed")
            return False

    def restart(self) -> None:
        """Replace the current listener and reset pending movement state."""

        with self._lifecycle_lock:
            listener = self._listener
            self._listener = None
        if listener is not None:
            try:
                listener.stop()
            except Exception:
                self._logger.debug("Mouse listener stop during restart failed", exc_info=True)
            try:
                listener.join(1.0)
            except Exception:
                self._logger.debug("Mouse listener join during restart failed", exc_info=True)
        self._movement_filter.reset()
        self.start()
        self._logger.warning("Mouse activity monitor restarted")

    def _on_move(self, _x: int, _y: int) -> None:
        try:
            if self._movement_filter.accepts_move():
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
        self._movement_filter.reset()
        try:
            self._activity_manager.record(ActivityKind.MOUSE_CLICK)
        except Exception:
            self._logger.exception("Mouse click activity update failed")

    @staticmethod
    def _default_factory() -> ListenerFactory:
        from pynput import mouse

        return mouse.Listener
