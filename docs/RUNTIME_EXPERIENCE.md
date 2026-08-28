# Runtime Experience — M5

M5 adds local Windows runtime controls without expanding Sentinel Lock beyond
keyboard and mouse activity.

## System tray

On Windows, the default runtime starts a small system tray icon. Its menu exposes:

- **Status** — active idle duration or lock-request state;
- **Lock now** — queues a lock request for the existing controller thread;
- **Exit** — requests graceful application shutdown.

The tray never calls the Windows locking API directly. `Lock now` sets a
thread-safe request event; `IdleLockController` consumes that request on its own
loop and uses the normal workstation locker boundary.

Disable the tray with:

```powershell
sentinel-lock --no-tray
```

## Desktop notifications

When the tray backend supports notifications, Sentinel Lock can report:

- a workstation lock request;
- idle-timer reset after a resume-like runtime gap.

Notifications contain operational state only. They do not contain keys, mouse
buttons, pointer coordinates, application names, or user content.

Disable notifications while keeping the tray:

```powershell
sentinel-lock --no-notifications
```

## Windows startup registration

Sentinel Lock can create one per-user entry under the standard Windows `Run`
registry key. Administrator privileges are not required for the current-user
entry.

```powershell
sentinel-lock --install-startup
sentinel-lock --startup-status
sentinel-lock --remove-startup
```

When `--install-startup` is used with runtime options such as `--config`,
`--timeout`, `--poll-interval`, `--dry-run`, `--no-tray`, or
`--no-notifications`, those runtime options are preserved in the registered
command.

## Suspend and resume handling

The runtime samples local monotonic and wall clocks once per controller loop. A
gap of at least 10 seconds, or four polling intervals when that is larger, is
treated as a resume-like discontinuity.

On detection:

1. the controller rearms itself;
2. the effective idle baseline is reset to the resume time;
3. no fake keyboard or mouse activity is inserted;
4. the Activity Manager sequence remains unchanged;
5. a later real keyboard/mouse event clears the resume baseline normally.

This also safely handles an unusually long process stall. Treating a long gap as
resume is conservative: it prevents an immediate lock based only on stale elapsed
time after the runtime was not executing normally.

## Privacy boundary

Runtime status contains only:

- controller state (`active` or `locked`);
- effective idle seconds;
- a count of resume-like discontinuities for the current process.

It does not expose or retain raw keyboard/mouse content. M5 adds no camera,
Bluetooth, microphone, location, network-presence, or trusted-device signal.
