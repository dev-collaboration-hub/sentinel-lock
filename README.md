# Sentinel Lock

> Privacy-first automatic workstation locking for Windows using keyboard and mouse activity only.

Sentinel Lock is implemented with Python 3.11+ standard-library code plus native
Windows APIs exposed by the operating system. It has **no pip dependencies** and
does not require `pynput`, `pystray`, Pillow, PyInstaller, setuptools, or any
other third-party Python package.

## Scope

Sentinel Lock intentionally uses only:

- keyboard key-press activity;
- meaningful mouse movement activity;
- mouse click activity.

Camera presence detection, face recognition, Bluetooth proximity, trusted-device
presence, microphone sensing, and other external presence signals are outside the
project scope.

## Scratch / dependency boundary

Application logic and Windows integration code live in this repository. Native
Windows functionality is accessed directly with Python `ctypes` and stdlib
modules:

- `SetWindowsHookExW` / `CallNextHookEx` for keyboard and mouse occurrence hooks;
- `Shell_NotifyIconW` plus a Win32 hidden-window message loop for tray controls and notifications;
- `LockWorkStation` for native workstation locking;
- `winreg` with `HKEY_CURRENT_USER` for optional per-user startup registration.

The hook adapters deliberately do not dereference keyboard payloads, pointer
coordinates, or mouse-button identity. Only minimal activity categories reach
application state.

## Current status

Implemented:

- scratch Win32 keyboard and mouse hook listeners;
- thread-safe keyboard and mouse activity tracking;
- deterministic isolated-movement filtering;
- meaningful movement confirmation using two callbacks within 250 ms;
- continuous mouse-movement refresh limited to once every 500 ms;
- configurable idle detection;
- direct `LockWorkStation` integration;
- one lock request per idle episode;
- listener health checks and recovery;
- scratch Win32 tray with Status, Lock now, Exit, and local notifications;
- per-user Windows startup registration;
- resume-like gap detection with safe idle re-baselining;
- high-frequency CPU/memory regression tests;
- long-run duplicate-lock stability tests;
- pip-free CI and release validation;
- stdlib `zipapp` release artifact with SHA-256 checksum.

## Requirements

- Windows 10 or Windows 11
- Python 3.11 or newer
- no pip packages

## Quick start from source

No installation is required:

```powershell
python .\run_sentinel_lock.py --config config/default.toml
```

Safe dry run:

```powershell
python .\run_sentinel_lock.py --dry-run --timeout 10
```

Validate configuration:

```powershell
python .\run_sentinel_lock.py --config config/default.toml --check-config
```

Optional runtime commands:

```powershell
python .\run_sentinel_lock.py --no-tray
python .\run_sentinel_lock.py --no-notifications
python .\run_sentinel_lock.py --install-startup
python .\run_sentinel_lock.py --startup-status
python .\run_sentinel_lock.py --remove-startup
```

## Stdlib release artifact

Build a single-file Python zip application using only the standard library:

```powershell
New-Item -ItemType Directory -Force dist | Out-Null
python -m zipapp src -m "sentinel_lock.cli:main" -o dist/sentinel-lock.pyz
python .\dist\sentinel-lock.pyz --version
```

The `.pyz` artifact still requires Python 3.11+ on the Windows machine. Sentinel
Lock intentionally does not bundle a third-party frozen Python runtime.

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

## Project structure

```text
sentinel-lock/
├── config/
├── docs/
├── run_sentinel_lock.py       No-install source launcher
├── src/sentinel_lock/
│   ├── monitors/              Keyboard/mouse policy adapters
│   ├── win32_input.py         Scratch low-level Win32 input hooks
│   ├── win32_tray.py          Scratch notification-area backend
│   ├── activity.py            Minimal activity state
│   ├── idle.py                Idle and lock policy
│   ├── locker.py              Direct LockWorkStation adapter
│   ├── reliability.py         Listener recovery supervisor
│   ├── resume.py              Resume-gap detection
│   ├── runtime_ui.py          Runtime UI boundary
│   └── startup.py             Per-user startup registration
└── tests/
```

## Dependency proof

CI runs:

```powershell
python tests/check_stdlib_only.py
python -m unittest discover -s tests -v
python -m compileall -q src tests run_sentinel_lock.py
```

`check_stdlib_only.py` rejects non-stdlib imports in application source, non-empty
pip requirements, `pip install` workflow steps, and the removed third-party
input/tray/packaging libraries.

## Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [Stdlib-only boundary](docs/STDLIB_ONLY.md)
- [Runtime Experience](docs/RUNTIME_EXPERIENCE.md)
- [Reliability and Performance](docs/M6_RELIABILITY.md)
- [Install, Upgrade, Remove](docs/INSTALL_UPGRADE_REMOVE.md)
- [Release validation](docs/RELEASE_VALIDATION.md)
- [Security model](docs/SECURITY.md)
- [Threat model](docs/THREAT_MODEL.md)
- [Roadmap](docs/ROADMAP.md)

## License

Sentinel Lock is licensed under the [MIT License](LICENSE).
