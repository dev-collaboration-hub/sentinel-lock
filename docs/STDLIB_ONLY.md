# Stdlib-only scratch boundary

Sentinel Lock has no pip/runtime package dependencies.

Allowed foundations:

- Python 3.11+ standard library;
- Windows system DLLs and APIs already provided by the operating system;
- repository-owned source code.

Not allowed in application/runtime code:

- third-party Python packages;
- package-installed input hooks;
- package-installed tray/UI libraries;
- frozen-app packagers as a runtime/build requirement;
- hidden network services or hosted APIs.

## Native Windows calls

The repository implements the platform adapters directly with `ctypes`:

- keyboard: `SetWindowsHookExW(WH_KEYBOARD_LL, ...)`;
- mouse: `SetWindowsHookExW(WH_MOUSE_LL, ...)`;
- hook chaining: `CallNextHookEx`;
- hook teardown: `UnhookWindowsHookEx`;
- hook thread shutdown: `PostThreadMessageW(WM_QUIT, ...)`;
- tray: hidden Win32 window + `Shell_NotifyIconW`;
- lock: `LockWorkStation`;
- startup: stdlib `winreg` under `HKEY_CURRENT_USER`.

These are Win32 APIs, not hand-issued raw NT kernel syscalls.

## Privacy rule

The native low-level hooks intentionally do not dereference keyboard hook payloads
or mouse pointer structures. Keyboard activity passes only a press occurrence.
Mouse movement passes only an occurrence into the existing timing filter. Button
identity and coordinates are discarded.

## Packaging

The release artifact is built with the Python standard-library `zipapp` module:

```powershell
python -m zipapp src -m "sentinel_lock.cli:main" -o dist/sentinel-lock.pyz
```

This artifact requires Python 3.11+ on the target Windows machine. The project no
longer uses a third-party frozen executable packager.

## CI enforcement

`tests/check_stdlib_only.py` parses every application source file and rejects any
import root outside the standard library or `sentinel_lock`. It also rejects pip
installation steps and former third-party dependency names in application code.

Normal CI runs this gate on Windows and Ubuntu before tests.
