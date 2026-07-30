"""Sentinel Lock workstation security package."""

from sentinel_lock.activity import ActivityKind, ActivityManager, ActivitySnapshot
from sentinel_lock.config import AppConfig, ConfigError, load_config

__all__ = [
    "ActivityKind",
    "ActivityManager",
    "ActivitySnapshot",
    "AppConfig",
    "ConfigError",
    "load_config",
]

__version__ = "0.1.0"
