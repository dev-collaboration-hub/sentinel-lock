"""Sentinel Lock runtime orchestration."""

from __future__ import annotations

import logging
from threading import Event
from typing import Any, Iterable

from sentinel_lock.activity import ActivityManager
from sentinel_lock.config import AppConfig
from sentinel_lock.idle import IdleLockController, WorkstationLocker
from sentinel_lock.locker import DryRunWorkstationLocker, WindowsWorkstationLocker
from sentinel_lock.monitors import InputMonitor, KeyboardMonitor, MouseMonitor
from sentinel_lock.resume import ResumeDetector


class SentinelLockApplication:
    """Own monitors, runtime experience, lock controller, and shutdown lifecycle."""

    def __init__(
        self,
        config: AppConfig,
        *,
        dry_run: bool = False,
        activity_manager: ActivityManager | None = None,
        monitors: Iterable[InputMonitor] | None = None,
        locker: WorkstationLocker | None = None,
        runtime_experience: Any | None = None,
        resume_detector: Any | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        self._config = config
        self._logger = logger or logging.getLogger(__name__)
        self._activity_manager = activity_manager or ActivityManager()
        self._monitors = list(monitors) if monitors is not None else [
            KeyboardMonitor(self._activity_manager),
            MouseMonitor(self._activity_manager),
        ]
        self._runtime_experience = runtime_experience

        if locker is None:
            locker = (
                DryRunWorkstationLocker(self._logger)
                if dry_run
                else WindowsWorkstationLocker()
            )

        if resume_detector is None:
            resume_detector = ResumeDetector(
                gap_seconds=max(10.0, config.runtime.poll_interval_seconds * 4.0)
            )

        evaluation_observer = (
            runtime_experience.observe if runtime_experience is not None else None
        )
        resume_observer = (
            runtime_experience.note_resume if runtime_experience is not None else None
        )
        self._controller = IdleLockController(
            self._activity_manager,
            locker,
            idle_timeout_seconds=config.security.idle_timeout_seconds,
            poll_interval_seconds=config.runtime.poll_interval_seconds,
            resume_detector=resume_detector,
            evaluation_observer=evaluation_observer,
            resume_observer=resume_observer,
            logger=self._logger,
        )

    def run(self, stop_event: Event | None = None) -> None:
        """Start monitors and runtime UI, then run until interrupted or stopped."""

        stop_event = stop_event or Event()
        started: list[InputMonitor] = []
        runtime_started = False
        try:
            for monitor in self._monitors:
                monitor.start()
                started.append(monitor)

            if self._runtime_experience is not None:
                runtime_started = bool(
                    self._runtime_experience.start(self._controller, stop_event)
                )

            self._logger.info(
                "Sentinel Lock started with %.1f second idle timeout",
                self._config.security.idle_timeout_seconds,
            )
            self._controller.run(stop_event)
        finally:
            if runtime_started:
                self._runtime_experience.stop()
            for monitor in reversed(started):
                monitor.stop()
            for monitor in reversed(started):
                monitor.join(timeout=2.0)
            self._logger.info("Sentinel Lock stopped")
