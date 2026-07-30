"""Sentinel Lock runtime orchestration."""

from __future__ import annotations

import logging
from threading import Event
from typing import Iterable

from sentinel_lock.activity import ActivityManager
from sentinel_lock.config import AppConfig
from sentinel_lock.idle import IdleLockController, WorkstationLocker
from sentinel_lock.locker import DryRunWorkstationLocker, WindowsWorkstationLocker
from sentinel_lock.monitors import InputMonitor, KeyboardMonitor, MouseMonitor


class SentinelLockApplication:
    """Own monitor, controller, and shutdown lifecycles."""

    def __init__(
        self,
        config: AppConfig,
        *,
        dry_run: bool = False,
        activity_manager: ActivityManager | None = None,
        monitors: Iterable[InputMonitor] | None = None,
        locker: WorkstationLocker | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        self._config = config
        self._logger = logger or logging.getLogger(__name__)
        self._activity_manager = activity_manager or ActivityManager()
        self._monitors = list(monitors) if monitors is not None else [
            KeyboardMonitor(self._activity_manager),
            MouseMonitor(self._activity_manager),
        ]
        selected_locker = locker
        if selected_locker is None:
            selected_locker = (
                DryRunWorkstationLocker(self._logger)
                if dry_run
                else WindowsWorkstationLocker()
            )
        self._controller = IdleLockController(
            self._activity_manager,
            selected_locker,
            idle_timeout_seconds=config.security.idle_timeout_seconds,
            poll_interval_seconds=config.runtime.poll_interval_seconds,
            logger=self._logger,
        )

    def run(self, stop_event: Event | None = None) -> None:
        """Start required monitors and run until interrupted or stopped."""

        stop_event = stop_event or Event()
        started: list[InputMonitor] = []
        try:
            for monitor in self._monitors:
                monitor.start()
                started.append(monitor)
            self._logger.info(
                "Sentinel Lock started with %.1f second idle timeout",
                self._config.security.idle_timeout_seconds,
            )
            self._controller.run(stop_event)
        finally:
            for monitor in reversed(started):
                monitor.stop()
            for monitor in reversed(started):
                monitor.join(timeout=2.0)
            self._logger.info("Sentinel Lock stopped")
