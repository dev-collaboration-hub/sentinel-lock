"""Simple smart-lock decision policy."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PresenceSignals:
    """Optional local signals that can keep an attended workstation unlocked."""

    user_present: bool | None = None
    trusted_device_nearby: bool | None = None


class SmartLockDecisionEngine:
    """Combine idle time with optional local presence signals."""

    def __init__(self, idle_timeout_seconds: float) -> None:
        if idle_timeout_seconds <= 0:
            raise ValueError("idle_timeout_seconds must be positive")
        self._idle_timeout_seconds = idle_timeout_seconds

    def should_lock(
        self,
        idle_seconds: float,
        signals: PresenceSignals | None = None,
    ) -> bool:
        """Return True when the workstation should be locked."""

        if idle_seconds < self._idle_timeout_seconds:
            return False

        signals = signals or PresenceSignals()
        if signals.user_present is True:
            return False
        if signals.trusted_device_nearby is True:
            return False
        return True
