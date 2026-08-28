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
from sentinel_lock.runtime_ui import TrayRuntimeExperience
from sentinel_lock.startup import (
    StartupRegistrationError,
    build_startup_command,
    install_startup,
    remove_startup,
    startup_command,
)


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
        "--no-tray",
        action="store_true",
        help="run without the Windows system tray controls",
    )
    parser.add_argument(
        "--no-notifications",
        action="store_true",
        help="disable desktop notifications from the tray runtime",
    )
    startup_group = parser.add_mutually_exclusive_group()
    startup_group.add_argument(
        "--install-startup",
        action="store_true",
        help="start Sentinel Lock automatically at Windows sign-in",
    )
    startup_group.add_argument(
        "--remove-startup",
        action="store_true",
        help="remove the per-user Windows startup entry",
    )
    startup_group.add_argument(
        "--startup-status",
        action="store_true",
        help="show the current per-user Windows startup entry",
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

    startup_result = _handle_startup_action(args)
    if startup_result is not None:
        return startup_result

    if args.check_config:
        _print_config_summary(
            config,
            dry_run=args.dry_run,
            tray_enabled=not args.no_tray,
            notifications_enabled=not args.no_notifications,
        )
        return 0

    try:
        logger = configure_logging(config.logging)
    except OSError as exc:
        print(f"sentinel-lock: cannot configure logging: {exc}", file=sys.stderr)
        return 2

    runtime_experience = None
    if sys.platform == "win32" and not args.no_tray:
        runtime_experience = TrayRuntimeExperience(
            notifications_enabled=not args.no_notifications,
            logger=logger,
        )

    try:
        application = SentinelLockApplication(
            config,
            dry_run=args.dry_run,
            runtime_experience=runtime_experience,
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


def _handle_startup_action(args: argparse.Namespace) -> int | None:
    if not (args.install_startup or args.remove_startup or args.startup_status):
        return None
    try:
        if args.install_startup:
            startup_args = _runtime_argv_for_startup(args)
            command = install_startup(build_startup_command(startup_args))
            print("Startup registration installed")
            print(command)
            return 0
        if args.remove_startup:
            removed = remove_startup()
            print("Startup registration removed" if removed else "Startup registration not present")
            return 0
        command = startup_command()
        if command is None:
            print("Startup registration: not installed")
        else:
            print("Startup registration: installed")
            print(command)
        return 0
    except StartupRegistrationError as exc:
        print(f"sentinel-lock: {exc}", file=sys.stderr)
        return 2


def _runtime_argv_for_startup(args: argparse.Namespace) -> list[str]:
    result: list[str] = []
    if args.config is not None:
        result.extend(["--config", str(args.config)])
    if args.timeout is not None:
        result.extend(["--timeout", str(args.timeout)])
    if args.poll_interval is not None:
        result.extend(["--poll-interval", str(args.poll_interval)])
    if args.dry_run:
        result.append("--dry-run")
    if args.no_tray:
        result.append("--no-tray")
    if args.no_notifications:
        result.append("--no-notifications")
    return result


def _print_config_summary(
    config: AppConfig,
    *,
    dry_run: bool,
    tray_enabled: bool,
    notifications_enabled: bool,
) -> None:
    log_file = str(config.logging.file) if config.logging.file else "console only"
    print("Configuration is valid")
    print(f"Idle timeout: {config.security.idle_timeout_seconds:g} seconds")
    print(f"Poll interval: {config.runtime.poll_interval_seconds:g} seconds")
    print(f"Logging: {config.logging.level} ({log_file})")
    print(f"Mode: {'dry run' if dry_run else 'native lock'}")
    print(f"System tray: {'enabled' if tray_enabled else 'disabled'}")
    print(
        f"Desktop notifications: {'enabled' if notifications_enabled else 'disabled'}"
    )


if __name__ == "__main__":
    logging.basicConfig()
    raise SystemExit(main())
