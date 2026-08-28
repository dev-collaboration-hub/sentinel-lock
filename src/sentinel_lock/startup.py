"""Per-user Windows startup registration."""

from __future__ import annotations

import os
import subprocess
import sys
from typing import Any, Sequence

RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
VALUE_NAME = "SentinelLock"


class StartupRegistrationError(RuntimeError):
    """Raised when Windows startup registration cannot be changed."""


def build_startup_command(argv: Sequence[str] | None = None) -> str:
    """Build a safely quoted command for starting Sentinel Lock at sign-in."""

    parts = [sys.executable, "-m", "sentinel_lock"]
    if argv:
        parts.extend(argv)
    return subprocess.list2cmdline(parts)


def install_startup(
    command: str | None = None,
    *,
    registry: Any | None = None,
) -> str:
    """Register Sentinel Lock under the current user's Windows Run key."""

    registry = _registry_module(registry)
    command = command or build_startup_command()
    try:
        with registry.CreateKey(registry.HKEY_CURRENT_USER, RUN_KEY) as key:
            registry.SetValueEx(key, VALUE_NAME, 0, registry.REG_SZ, command)
    except OSError as exc:
        raise StartupRegistrationError(f"cannot install startup entry: {exc}") from exc
    return command


def remove_startup(*, registry: Any | None = None) -> bool:
    """Remove the current user's startup entry; return whether it existed."""

    registry = _registry_module(registry)
    try:
        with registry.OpenKey(
            registry.HKEY_CURRENT_USER,
            RUN_KEY,
            0,
            registry.KEY_SET_VALUE,
        ) as key:
            registry.DeleteValue(key, VALUE_NAME)
    except FileNotFoundError:
        return False
    except OSError as exc:
        raise StartupRegistrationError(f"cannot remove startup entry: {exc}") from exc
    return True


def startup_command(*, registry: Any | None = None) -> str | None:
    """Return the configured startup command, if one exists."""

    registry = _registry_module(registry)
    try:
        with registry.OpenKey(registry.HKEY_CURRENT_USER, RUN_KEY) as key:
            value, value_type = registry.QueryValueEx(key, VALUE_NAME)
    except FileNotFoundError:
        return None
    except OSError as exc:
        raise StartupRegistrationError(f"cannot read startup entry: {exc}") from exc
    if value_type != registry.REG_SZ or not isinstance(value, str):
        raise StartupRegistrationError("startup entry has an unexpected registry type")
    return value


def _registry_module(registry: Any | None) -> Any:
    if registry is not None:
        return registry
    if os.name != "nt":
        raise StartupRegistrationError("startup registration is only supported on Windows")
    import winreg

    return winreg
