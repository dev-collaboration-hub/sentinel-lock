"""Validated TOML configuration for Sentinel Lock."""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any
import tomllib

MIN_IDLE_TIMEOUT_SECONDS = 5.0
MAX_IDLE_TIMEOUT_SECONDS = 86_400.0
MIN_POLL_INTERVAL_SECONDS = 0.1
MAX_POLL_INTERVAL_SECONDS = 60.0
VALID_LOG_LEVELS = frozenset({"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"})


class ConfigError(ValueError):
    """Raised when configuration cannot be parsed or validated."""


@dataclass(frozen=True, slots=True)
class SecurityConfig:
    idle_timeout_seconds: float = 300.0


@dataclass(frozen=True, slots=True)
class RuntimeConfig:
    poll_interval_seconds: float = 1.0


@dataclass(frozen=True, slots=True)
class LoggingConfig:
    level: str = "INFO"
    file: Path | None = Path("logs/sentinel-lock.log")
    max_bytes: int = 1_048_576
    backup_count: int = 3


@dataclass(frozen=True, slots=True)
class AppConfig:
    security: SecurityConfig = SecurityConfig()
    runtime: RuntimeConfig = RuntimeConfig()
    logging: LoggingConfig = LoggingConfig()


_ALLOWED_KEYS = {
    "security": frozenset({"idle_timeout_seconds"}),
    "runtime": frozenset({"poll_interval_seconds"}),
    "logging": frozenset({"level", "file", "max_bytes", "backup_count"}),
}


def load_config(path: str | Path | None = None) -> AppConfig:
    """Load and validate configuration, or return built-in defaults."""

    if path is None:
        return AppConfig()

    config_path = Path(path)
    try:
        with config_path.open("rb") as config_file:
            raw = tomllib.load(config_file)
    except FileNotFoundError as exc:
        raise ConfigError(f"configuration file not found: {config_path}") from exc
    except (OSError, tomllib.TOMLDecodeError) as exc:
        raise ConfigError(f"cannot read configuration {config_path}: {exc}") from exc

    if not isinstance(raw, dict):
        raise ConfigError("configuration root must be a TOML table")
    _reject_unknown_keys(raw)

    security_raw = _table(raw, "security")
    runtime_raw = _table(raw, "runtime")
    logging_raw = _table(raw, "logging")

    security = SecurityConfig(
        idle_timeout_seconds=_number(
            security_raw.get("idle_timeout_seconds", 300.0),
            "security.idle_timeout_seconds",
            MIN_IDLE_TIMEOUT_SECONDS,
            MAX_IDLE_TIMEOUT_SECONDS,
        )
    )
    runtime = RuntimeConfig(
        poll_interval_seconds=_number(
            runtime_raw.get("poll_interval_seconds", 1.0),
            "runtime.poll_interval_seconds",
            MIN_POLL_INTERVAL_SECONDS,
            MAX_POLL_INTERVAL_SECONDS,
        )
    )
    logging_config = LoggingConfig(
        level=_log_level(logging_raw.get("level", "INFO")),
        file=_log_path(logging_raw.get("file", "logs/sentinel-lock.log")),
        max_bytes=_integer(
            logging_raw.get("max_bytes", 1_048_576),
            "logging.max_bytes",
            1_024,
            104_857_600,
        ),
        backup_count=_integer(
            logging_raw.get("backup_count", 3),
            "logging.backup_count",
            0,
            20,
        ),
    )
    return AppConfig(
        security=security,
        runtime=runtime,
        logging=logging_config,
    )


def apply_overrides(
    config: AppConfig,
    *,
    idle_timeout_seconds: float | None = None,
    poll_interval_seconds: float | None = None,
) -> AppConfig:
    """Return a validated copy containing command-line overrides."""

    security = config.security
    runtime = config.runtime
    if idle_timeout_seconds is not None:
        security = replace(
            security,
            idle_timeout_seconds=_number(
                idle_timeout_seconds,
                "timeout",
                MIN_IDLE_TIMEOUT_SECONDS,
                MAX_IDLE_TIMEOUT_SECONDS,
            ),
        )
    if poll_interval_seconds is not None:
        runtime = replace(
            runtime,
            poll_interval_seconds=_number(
                poll_interval_seconds,
                "poll interval",
                MIN_POLL_INTERVAL_SECONDS,
                MAX_POLL_INTERVAL_SECONDS,
            ),
        )
    return replace(config, security=security, runtime=runtime)


def _reject_unknown_keys(raw: dict[str, Any]) -> None:
    unknown_sections = set(raw) - set(_ALLOWED_KEYS)
    if unknown_sections:
        names = ", ".join(sorted(unknown_sections))
        raise ConfigError(f"unknown configuration section(s): {names}")

    for section, allowed in _ALLOWED_KEYS.items():
        value = raw.get(section, {})
        if not isinstance(value, dict):
            raise ConfigError(f"{section} must be a TOML table")
        unknown = set(value) - set(allowed)
        if unknown:
            names = ", ".join(f"{section}.{key}" for key in sorted(unknown))
            raise ConfigError(f"unknown configuration key(s): {names}")


def _table(raw: dict[str, Any], name: str) -> dict[str, Any]:
    value = raw.get(name, {})
    if not isinstance(value, dict):
        raise ConfigError(f"{name} must be a TOML table")
    return value


def _number(value: Any, name: str, minimum: float, maximum: float) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ConfigError(f"{name} must be a number")
    result = float(value)
    if not minimum <= result <= maximum:
        raise ConfigError(f"{name} must be between {minimum:g} and {maximum:g}")
    return result


def _integer(value: Any, name: str, minimum: int, maximum: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ConfigError(f"{name} must be an integer")
    if not minimum <= value <= maximum:
        raise ConfigError(f"{name} must be between {minimum} and {maximum}")
    return value


def _log_level(value: Any) -> str:
    if not isinstance(value, str):
        raise ConfigError("logging.level must be a string")
    level = value.upper()
    if level not in VALID_LOG_LEVELS:
        valid = ", ".join(sorted(VALID_LOG_LEVELS))
        raise ConfigError(f"logging.level must be one of: {valid}")
    return level


def _log_path(value: Any) -> Path | None:
    if not isinstance(value, str):
        raise ConfigError("logging.file must be a string")
    value = value.strip()
    return Path(value) if value else None
