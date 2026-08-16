# Sentinel Lock

> Privacy-first adaptive workstation locking for Windows.

Sentinel Lock protects an unattended Windows workstation using lightweight local
signals. Keyboard and mouse inactivity provide the working baseline. Optional
presence and trusted-device signals can delay locking without being coupled to
the Windows locking code.

## Current status

Implemented today:

- thread-safe keyboard and mouse activity tracking;
- configurable idle detection;
- native Windows workstation locking;
- simple lock decision logic for idle time and optional local signals;
- optional `user_present` and `trusted_device_nearby` inputs;
- graceful background-service lifecycle;
- rotating operational logs with no raw input data;
- dry-run configuration checks;
- unit tests for activity, timing, lock decisions, and failure handling.

If no extra presence signal is connected, Sentinel Lock keeps the existing
idle-time behavior. Unknown or failed optional signals do not disable baseline
protection.

## Project direction

Sentinel Lock is not limited to keyboard and mouse inactivity. Future optional
local adapters can provide signals from:

- computer-vision presence detection;
- local face recognition;
- Bluetooth phone proximity;
- trusted-device detection;
- system tray controls and desktop notifications;
- cross-platform support.

These adapters should remain optional and local-first. Raw keystrokes, pointer
coordinates, camera frames, and private user content must not be logged or sent
remotely by the core application.

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
│   ├── idle.py              Idle tracking and lock decision logic
│   ├── locker.py            Windows locking adapter
│   └── logging_setup.py     Privacy-safe rotating logs
└── tests/                   Cross-platform unit tests
```

## Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [Activity Manager module](docs/modules/ACTIVITY_MANAGER.md)
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
changes small, include tests, and preserve the privacy-first local architecture.

## License

Sentinel Lock is licensed under the [MIT License](LICENSE).
