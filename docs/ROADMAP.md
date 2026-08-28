# Roadmap

Sentinel Lock is intentionally limited to keyboard and mouse activity. Camera,
face recognition, Bluetooth proximity, trusted-device presence, microphone
sensing, and other external presence signals are out of scope.

## M1 — Activity Monitoring

- keyboard press activity;
- mouse movement activity;
- mouse click activity;
- thread-safe centralized activity state;
- deterministic listener tests.

Status: implemented.

## M2 — Idle Detection and Windows Locking

- configurable monotonic idle timer;
- one lock request per idle episode;
- recovery after new keyboard or mouse activity;
- native `LockWorkStation` adapter;
- dry-run safety mode;
- deterministic threshold and failure tests.

Status: implemented.

## M3 — Keyboard/Mouse Lock Core

- keep keyboard and mouse activity as the only activity sources;
- use one small deterministic idle-lock decision path;
- lock when the configured inactivity threshold is reached;
- rearm after new keyboard or mouse activity;
- preserve privacy by discarding raw input content.

Status: implemented.

## M4 — Advanced Keyboard and Mouse Activity Detection

- filter isolated mouse-movement jitter without retaining pointer coordinates;
- confirm meaningful movement with two callbacks inside a 250 ms window;
- rate-limit continuous movement activity refresh to once every 500 ms;
- preserve immediate keyboard and pressed-click activity updates;
- reset pending movement confirmation after a pressed click;
- add deterministic tests for filtering, refresh behavior, and privacy boundaries;
- document the exact movement rules and constants.

Status: implemented.

## M5 — Runtime Experience

- Windows system tray with privacy-safe Status, Lock now, and Exit controls;
- desktop notifications for lock requests and resume re-baselining;
- optional per-user Windows startup registration and status/removal commands;
- suspend/resume-like gap detection with safe idle re-baselining;
- clear idle and lock status without exposing private input data;
- deterministic tests for runtime controls, resume behavior, startup registration,
  lifecycle, and privacy-safe status.

Status: implemented.

## M6 — Reliability and Performance

- high-frequency keyboard and mouse stress tests with deterministic CI guards;
- built-in listener health probing and restart after transient input-hook failure;
- retry on a later poll after transient restart failure;
- bounded process-CPU and Python traced-memory regression ceilings;
- 1,000-episode long-run stability simulation;
- protection against duplicate automatic and runtime-requested locks;
- validation that M4 movement filtering remains bounded under high event rates;
- dedicated reliability and performance evidence documentation.

Status: implemented.

## M7 — Release Hardening

- signed Windows packaging;
- multi-user validation;
- accessibility and power-consumption testing;
- threat-model review;
- installation, upgrade, and removal documentation;
- stable v1.0 release.

Status: planned.
