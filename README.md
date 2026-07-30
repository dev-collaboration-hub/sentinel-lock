# Sentinel Lock

> Privacy-first automatic workstation locking for Windows.

Sentinel Lock protects an unattended Windows workstation by monitoring local
keyboard and mouse activity and locking the session after a configurable idle
period. Activity is processed in memory; the application does not record keys,
buttons, pointer coordinates, or user content.

## Status

The initial MVP provides:

- thread-safe keyboard and mouse activity tracking;
- configurable idle detection;
- native Windows workstation locking;
- graceful background-service lifecycle;
- rotating operational logs with no raw input data;
- a dry-run mode for safe configuration checks;
- unit tests for the core security and timing logic.

The project scope is intentionally limited to keyboard activity, mouse activity,
idle-time evaluation, and Windows workstation locking.

## Requirements

- Windows 10 or Windows 11
- Python 3.11 or newer

## Quick start

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
sentinel-lock --config config/default.toml
```

The default idle timeout is 300 seconds. To test without locking the machine:

```powershell
sentinel-lock --dry-run --timeout 10
```

Validate a configuration file and exit:

```powershell
sentinel-lock --config config/default.toml --check-config
```

Stop the foreground process with `Ctrl+C`.

## Configuration

```toml
[security]
idle_timeout_seconds = 300

[runtime]
poll_interval_seconds = 1.0

[logging]
level = "INFO"
file = "logs/sentinel-lock.log"
max_bytes = 1048576
backup_count = 3
```

Command-line `--timeout` and `--poll-interval` values override the file.
See [docs/CONFIGURATION.md](docs/CONFIGURATION.md) for validation rules and
operational guidance.

## Project structure

```text
sentinel-lock/
├── config/                  Default runtime configuration
├── docs/                    Architecture, security, and development guides
├── src/sentinel_lock/       Application package
│   ├── monitors/            Keyboard and mouse adapters
│   ├── activity.py          Thread-safe activity state
│   ├── app.py               Runtime orchestration
│   ├── cli.py               Command-line interface
│   ├── config.py            TOML configuration loader
│   ├── idle.py              Idle policy and lock controller
│   ├── locker.py            Windows locking adapter
│   └── logging_setup.py     Privacy-safe rotating logs
└── tests/                   Cross-platform unit tests
```

## Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [Configuration](docs/CONFIGURATION.md)
- [Security model](docs/SECURITY.md)
- [Development guide](docs/DEVELOPMENT.md)
- [Roadmap](docs/ROADMAP.md)

## Development

```powershell
python -m unittest discover -s tests -v
python -m compileall -q src tests
```

The test suite uses fake input listeners and a fake clock, so it does not lock
the workstation or require an active desktop session.

## Contributing

Read [CONTRIBUTING.md](CONTRIBUTING.md) before opening a pull request. Keep
changes small, include tests, and never add input-content logging or remote
telemetry.

## License

Sentinel Lock is licensed under the [MIT License](LICENSE).
