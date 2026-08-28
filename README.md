# Sentinel Lock

> Privacy-first automatic workstation locking for Windows using keyboard and mouse activity only.

Sentinel Lock protects an unattended Windows workstation with lightweight local
keyboard and mouse activity tracking. It records only minimal activity state and
locks the workstation after a configurable idle period.

## Scope

Sentinel Lock intentionally uses only:

- keyboard key-press activity;
- meaningful mouse movement activity;
- mouse click activity.

Camera presence detection, face recognition, Bluetooth proximity, trusted-device
presence, microphone sensing, and other external presence signals are outside the
project scope.

## Current status

Implemented today:

- thread-safe keyboard and mouse activity tracking;
- deterministic filtering of isolated mouse-movement jitter;
- meaningful movement confirmation using two callbacks within 250 ms;
- continuous mouse-movement refresh limited to once every 500 ms;
- immediate keyboard and pressed-click activity refresh;
- configurable idle detection;
- native Windows workstation locking;
- one lock request per idle episode;
- recovery after new accepted keyboard or mouse activity;
- Windows system tray with Status, Lock now, and Exit controls;
- privacy-safe desktop notifications;
- optional per-user Windows startup registration;
- resume-like gap detection with safe idle re-baselining;
- graceful background-service lifecycle;
- rotating operational logs with no raw input data;
- dry-run configuration checks;
- deterministic unit tests for activity, filtering, timing, runtime controls,
  startup registration, resume handling, lock decisions, and failure handling.

Raw key values, mouse buttons, pointer coordinates, and private user content are
not retained or sent remotely. Mouse movement filtering uses callback timing only;
it does not keep pointer positions.

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

The Windows tray is enabled by default. It shows the current idle/lock status and
provides **Lock now** and **Exit** controls. Optional runtime commands:

```powershell
sentinel-lock --no-tray
sentinel-lock --no-notifications
sentinel-lock --install-startup
sentinel-lock --startup-status
sentinel-lock --remove-startup
```

Stop a foreground process with `Ctrl+C` or use **Exit** from the tray.

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
│   ├── resume.py            Suspend/resume-like gap detection
│   ├── runtime_ui.py        Tray controls, status, and notifications
│   ├── startup.py           Per-user Windows startup registration
│   └── logging_setup.py     Privacy-safe rotating logs
└── tests/                   Cross-platform unit tests
```

## Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [Activity Manager module](docs/modules/ACTIVITY_MANAGER.md)
- [Mouse Monitor module / M4 rules](docs/modules/MOUSE_MONITOR.md)
- [Runtime Experience / M5](docs/RUNTIME_EXPERIENCE.md)
- [Configuration](docs/CONFIGURATION.md)
- [Security model](docs/SECURITY.md)
- [Development guide](docs/DEVELOPMENT.md)
- [Roadmap](docs/ROADMAP.md)

## Development

```powershell
python -m unittest discover -s tests -v
python -m compileall -q src tests
```

The test suite uses fake input listeners, clocks, lockers, and registry adapters,
so it does not lock the workstation or require an active desktop session.

## Contributing

Read [CONTRIBUTING.md](CONTRIBUTING.md) before opening a pull request. Keep
changes small, include tests, and preserve the keyboard/mouse-only privacy-first
architecture.

## License

Sentinel Lock is licensed under the [MIT License](LICENSE).
