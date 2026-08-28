# Runtime Experience — M5

M5 adds local Windows runtime controls without expanding Sentinel Lock beyond
keyboard and mouse activity. The current implementation uses no tray/UI package;
it talks to Win32 directly through `ctypes`.

## Native system tray

`Win32TrayBackend` owns a hidden Win32 window and message loop. It creates and
updates the notification-area icon with `Shell_NotifyIconW` and builds a native
popup menu with Win32 menu APIs.

The menu exposes:

- **Status** — active idle duration or lock-request state;
- **Lock now** — queues a lock request for the existing controller thread;
- **Exit** — requests graceful application shutdown.

The tray never calls `LockWorkStation` directly.

Disable the tray:

```powershell
python .\run_sentinel_lock.py --no-tray
```

## Desktop notifications

Native notification-area information messages can report:

- a workstation lock request;
- idle-timer reset after a resume-like runtime gap.

Notifications contain operational state only.

Disable notifications while keeping the tray:

```powershell
python .\run_sentinel_lock.py --no-notifications
```

## Windows startup registration

Sentinel Lock creates one per-user entry under the standard Windows `Run` key via
stdlib `winreg`.

Source checkout:

```powershell
python .\run_sentinel_lock.py --install-startup
python .\run_sentinel_lock.py --startup-status
python .\run_sentinel_lock.py --remove-startup
```

A `.pyz` release can use the same flags through `python sentinel-lock.pyz ...`.
The generated startup command points to the source launcher or current `.pyz`;
it does not assume a pip-installed console script.

## Suspend and resume handling

The runtime samples local monotonic and wall clocks once per controller loop. A
gap of at least 10 seconds, or four polling intervals when that is larger, is
treated as a resume-like discontinuity.

On detection:

1. the controller rearms itself;
2. effective idle time is re-baselined;
3. no fake keyboard or mouse activity is inserted;
4. the Activity Manager sequence remains unchanged;
5. later real input clears the resume baseline normally.

## Privacy boundary

Runtime status contains only controller state, effective idle seconds, and a
process-local resume count. It never exposes raw input.
