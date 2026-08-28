# Sentinel Lock Architecture

## Design goals

Sentinel Lock stays small, local-first, and keyboard/mouse-only:

1. **Fail safely:** failed lock requests are reported and retried.
2. **Remain lightweight:** input callbacks only update small in-memory state.
3. **Preserve privacy:** raw keyboard and mouse content is never retained.
4. **Stay testable:** clocks, monitors, runtime UI, registry access, recovery, and the locker are replaceable.
5. **Keep platform code separate:** lock decisions never call Windows APIs directly.
6. **Keep scope narrow:** only keyboard presses, meaningful mouse movement, and mouse clicks can refresh activity.

Camera, face recognition, Bluetooth proximity, trusted-device presence, microphone
sensing, and other external presence signals are not part of Sentinel Lock.

## Runtime flow

```mermaid
flowchart TD
    K["Keyboard listener"] --> A["Activity manager"]
    M["Mouse listener"] --> F["Movement timing filter"]
    F --> A
    M --> A
    K --> H["Monitor supervisor"]
    M --> H
    H -->|restart unhealthy listener| K
    H -->|restart unhealthy listener| M
    A --> C["Idle lock controller"]
    C --> H
    R["Resume gap detector"] --> C
    T["Tray controls"] -->|lock request event| C
    C --> S["Privacy-safe runtime status"]
    S --> T
    C --> L["Windows locker"]
    C --> O["Operational log"]
```

Keyboard presses and pressed mouse clicks update `ActivityManager` immediately.
Mouse movement first passes through a deterministic timing filter. The filter
confirms movement when two callbacks arrive within 250 ms and then limits
continuous movement refreshes to once every 500 ms.

`IdleLockController` calculates elapsed inactivity and requests a workstation
lock when the configured idle threshold is reached. New accepted activity
changes the activity sequence and rearms the controller for a future idle
episode.

The runtime-experience boundary stays outside the lock policy. Tray actions never
call Windows APIs directly. **Lock now** sets a thread-safe request event that the
controller consumes on its own loop. Runtime status contains only controller
state and effective idle duration.

M6 adds one lightweight maintenance callback to the same controller poll loop.
The callback invokes `MonitorSupervisor`, which checks only listener health and
may restart a failed built-in input monitor. It does not create activity events
or change lock thresholds.

## Components

### Activity manager

`sentinel_lock.activity.ActivityManager` stores the latest accepted keyboard or
mouse activity timestamp and sequence number. It never stores the key value,
mouse button, or pointer coordinates.

### Input monitors

`KeyboardMonitor` converts every key press into `KEYBOARD` activity without
retaining the pressed key.

`MouseMonitor` handles movement and clicks through one `pynput` listener:

- one isolated movement callback starts a candidate burst but does not refresh activity;
- a second callback within 250 ms confirms meaningful movement;
- confirmed continuous movement can refresh activity at most once every 500 ms;
- a gap longer than 250 ms starts a new candidate burst;
- pressed clicks refresh activity immediately and reset pending movement state;
- release callbacks are ignored.

Both built-in monitors expose a small lifecycle health contract:

- `is_alive()` probes whether the underlying listener is still running;
- `restart()` replaces a failed listener;
- mouse restart clears pending movement-filter timing state before starting the
  replacement listener.

The movement filter stores only monotonic timing state. Pointer `x` and `y`
values are ignored and never retained.

### Monitor supervisor

`sentinel_lock.reliability.MonitorSupervisor` polls recoverable monitors during
the controller's normal maintenance cycle. Healthy listeners are untouched.
Stopped listeners are restarted. A transient restart failure is logged and the
next poll can retry.

A custom monitor that does not expose both `is_alive()` and `restart()` is not
managed by the supervisor. Recovery errors are isolated from idle evaluation.

### Lock controller

`sentinel_lock.idle.IdleLockController` contains the runtime policy:

- do nothing before the idle timeout;
- request one lock when the timeout is reached;
- accept a thread-safe explicit lock request from the runtime UI;
- rearm after new accepted keyboard or mouse activity;
- re-baseline effective idle time after a resume-like discontinuity;
- call lightweight runtime maintenance once per normal poll;
- keep running after native-lock, resume-detector, maintenance, or observer failures.

The decision rule remains deterministic. There is no presence sensor,
trusted-device bypass, external signal reader, AI model, or separate rule engine.

### Resume detector

`sentinel_lock.resume.ResumeDetector` compares consecutive local monotonic and
wall-clock samples. A sufficiently long gap is treated as suspend/resume-like
runtime discontinuity.

The controller does not fabricate an activity event on resume. Instead, it keeps
the real Activity Manager sequence unchanged and temporarily caps effective idle
time at time-since-resume until genuine keyboard or mouse activity arrives.

### Runtime UI

`sentinel_lock.runtime_ui.TrayRuntimeExperience` is an optional Windows tray
layer. It exposes:

- privacy-safe Status text;
- **Lock now**;
- **Exit**;
- local desktop notifications when supported by the tray backend.

The tray receives controller evaluations through an observer callback. Its
`RuntimeStatus` stores only controller state, effective idle seconds, and a
process-local resume count. It has no raw input access.

### Windows startup registration

`sentinel_lock.startup` manages one per-user entry in the standard Windows
`Run` registry key. Registration preserves explicitly supplied runtime CLI
options and does not require an administrator-level machine-wide key.

### Windows locker

`WindowsWorkstationLocker` is the only component that calls the Windows lock
API. `DryRunWorkstationLocker` uses the same interface without changing session
state.

### Reliability and performance guards

M6 adds CI regression guards rather than claiming fixed end-user benchmark
numbers. Tests cover:

- 10,000 keyboard callbacks;
- 10,000 high-rate mouse movement callbacks;
- process CPU ceiling below 10 seconds for each stress test;
- Python traced peak-memory ceiling below 32 MiB for each stress test;
- 1,000 complete idle episodes with exact one-lock-per-episode behavior;
- transient listener restart failure followed by successful recovery;
- repeated runtime lock requests while already locked.

### Configuration and logging

TOML configures runtime values such as idle timeout, polling, and logging.
Configuration does not introduce additional activity sources.

Logs contain lifecycle, policy, recovery, and error information only. Raw
keystrokes, mouse buttons, pointer coordinates, and private user content must not
be logged.

## Scope boundary

The supported activity flow is fixed:

1. keyboard presses or mouse activity arrive through input monitors;
2. the mouse monitor filters isolated movement jitter using timing only;
3. monitors convert accepted input to minimal activity categories;
4. `ActivityManager` updates the latest activity state;
5. `MonitorSupervisor` may repair listener availability but cannot create activity;
6. `IdleLockController` evaluates inactivity and explicit local lock requests;
7. runtime status observes controller output without seeing raw input;
8. `WindowsWorkstationLocker` performs the platform lock action.

Startup registration, tray controls, notifications, resume handling, and monitor
recovery do not become new activity sources. Features that infer presence from
camera, face, Bluetooth, nearby devices, audio, location, or network state belong
outside this repository.
