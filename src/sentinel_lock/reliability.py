"""Small runtime reliability helpers for input-monitor recovery."""

from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import Iterable


@dataclass(frozen=True, slots=True)
class RecoveryReport:
    checked: int
    restarted: int
    failures: int


class MonitorSupervisor:
    """Poll recoverable monitors and restart listeners that have stopped."""

    def __init__(
        self,
        monitors: Iterable[object],
        *,
        logger: logging.Logger | None = None,
    ) -> None:
        self._monitors = tuple(monitors)
        self._logger = logger or logging.getLogger(__name__)

    def poll(self) -> RecoveryReport:
        checked = 0
        restarted = 0
        failures = 0

        for monitor in self._monitors:
            health_probe = getattr(monitor, "is_alive", None)
            restart = getattr(monitor, "restart", None)
            if not callable(health_probe) or not callable(restart):
                continue

            checked += 1
            try:
                healthy = bool(health_probe())
            except Exception:
                self._logger.exception("Input monitor health probe failed")
                healthy = False

            if healthy:
                continue

            self._logger.warning(
                "Input monitor stopped unexpectedly; attempting restart: %s",
                type(monitor).__name__,
            )
            try:
                restart()
            except Exception:
                failures += 1
                self._logger.exception(
                    "Input monitor restart failed: %s", type(monitor).__name__
                )
            else:
                restarted += 1

        return RecoveryReport(
            checked=checked,
            restarted=restarted,
            failures=failures,
        )
