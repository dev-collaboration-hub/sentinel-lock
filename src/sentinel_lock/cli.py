"""Command-line interface for Sentinel Lock."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path
import sys
from typing import Sequence

from sentinel_lock.app import SentinelLockApplication
from sentinel_lock.config import AppConfig, ConfigError, apply_overrides, load_config
from sentinel_lock.locker import UnsupportedPlatformError
from sentinel_lock.logging_setup import configure_logging
from sentinel_lock.monitors import MonitorStartError


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="sentinel-lock",
        description="Lock a Windows workstation after local input inactivity.",
    )
    parser.add_argument(
        "--config",
        type=Path,
        help="path to a TOML configuration file",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        help="idle timeout in seconds (overrides configuration)",
    )
    parser.add_argument(
        "--poll-interval",
        type=float,
        help="policy polling interval in seconds (overrides configuration)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="report lock decisions without locking the workstation",
    )
    parser.add_argument(
        "--check-config",
        action="store_true",
        help="validate effective configuration and exit",
    )
    parser.add_argument(
        "--version",
        action="version",
        version="sentinel-lock 0.1.0",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        config = load_config(args.config)
        config = apply_overrides(
            config,
            idle_timeout_seconds=args.timeout,
            poll_interval_seconds=args.poll_interval,
        )
    except ConfigError as exc:
        parser.error(str(exc))

    if args.check_config:
        _print_config_summary(config, dry_run=args.dry_run)
        return 0

    try:
        logger = configure_logging(config.logging)
    except OSError as exc:
        print(f"sentinel-lock: cannot configure logging: {exc}", file=sys.stderr)
        return 2

    try:
        application = SentinelLockApplication(
            config,
            dry_run=args.dry_run,
            logger=logger,
        )
        application.run()
    except (UnsupportedPlatformError, MonitorStartError) as exc:
        logger.error("%s", exc)
        return 2
    except KeyboardInterrupt:
        logger.info("Shutdown requested")
    except Exception:
        logger.exception("Sentinel Lock stopped because of an unexpected error")
        return 1
    return 0


def _print_config_summary(config: AppConfig, *, dry_run: bool) -> None:
    log_file = str(config.logging.file) if config.logging.file else "console only"
    print("Configuration is valid")
    print(f"Idle timeout: {config.security.idle_timeout_seconds:g} seconds")
    print(f"Poll interval: {config.runtime.poll_interval_seconds:g} seconds")
    print(f"Logging: {config.logging.level} ({log_file})")
    print(f"Mode: {'dry run' if dry_run else 'native lock'}")


if __name__ == "__main__":
    logging.basicConfig()
    raise SystemExit(main())
