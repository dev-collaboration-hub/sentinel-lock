"""Native and dry-run workstation lock adapters."""

from __future__ import annotations

import ctypes
from ctypes import wintypes
import logging
import sys
from typing import Callable


class UnsupportedPlatformError(RuntimeError):
    """Raised when native locking is requested outside Windows."""


class WorkstationLockError(OSError):
    """Raised when Windows rejects a workstation lock request."""


class WindowsWorkstationLocker:
    """Lock the current Windows session through ``LockWorkStation``."""

    def __init__(
        self,
        *,
        lock_api: Callable[[], int] | None = None,
        platform_name: str | None = None,
    ) -> None:
        platform_name = platform_name or sys.platform
        if platform_name != "win32":
            raise UnsupportedPlatformError(
                "native workstation locking is supported only on Windows; "
                "use --dry-run for a safe non-Windows check"
            )
        self._lock_api = lock_api or self._load_lock_api()

    def lock(self) -> None:
        result = self._lock_api()
        if not result:
            get_last_error = getattr(ctypes, "get_last_error", lambda: 0)
            error_code = get_last_error()
            detail = f"Windows error {error_code}" if error_code else "unknown error"
            raise WorkstationLockError(
                error_code, f"LockWorkStation failed: {detail}"
            )

    @staticmethod
    def _load_lock_api() -> Callable[[], int]:
        user32 = ctypes.WinDLL("user32", use_last_error=True)
        lock_workstation = user32.LockWorkStation
        lock_workstation.argtypes = []
        lock_workstation.restype = wintypes.BOOL
        return lock_workstation


class DryRunWorkstationLocker:
    """Log policy decisions without changing workstation state."""

    def __init__(self, logger: logging.Logger | None = None) -> None:
        self._logger = logger or logging.getLogger(__name__)

    def lock(self) -> None:
        self._logger.warning("Dry run: workstation lock would be requested")
