"""Shared monitor contracts."""

from __future__ import annotations

from typing import Protocol


class MonitorStartError(RuntimeError):
    """Raised when a required input monitor cannot start."""


class InputMonitor(Protocol):
    """Lifecycle implemented by input adapters."""

    def start(self) -> None:
        """Start receiving events."""

    def stop(self) -> None:
        """Request listener shutdown."""

    def join(self, timeout: float | None = None) -> None:
        """Wait for listener shutdown."""
