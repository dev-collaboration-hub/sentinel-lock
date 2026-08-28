# Roadmap

Sentinel Lock is intentionally limited to keyboard and mouse activity and is now
implemented with **Python standard library + Windows system APIs only**. There are
no pip/runtime package dependencies.

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

- keyboard and mouse remain the only activity sources;
- deterministic idle-lock decision path;
- lock at configured inactivity threshold;
- rearm after accepted input;
- discard raw input content.

Status: implemented.

## M4 — Advanced Keyboard and Mouse Activity Detection

- filter isolated mouse-movement jitter without retaining pointer coordinates;
- confirm meaningful movement with two callbacks inside 250 ms;
- rate-limit continuous movement refresh to once every 500 ms;
- preserve immediate keyboard and pressed-click activity;
- deterministic privacy and timing tests.

Status: implemented.

## M5 — Runtime Experience

- native Windows notification-area controls;
- Status, Lock now, and Exit;
- local notifications;
- optional per-user Windows startup registration;
- resume-like gap handling;
- privacy-safe status.

Status: implemented.

## M6 — Reliability and Performance

- high-frequency keyboard/mouse stress tests;
- listener health probing and restart;
- retry after transient hook restart failure;
- CPU/memory regression ceilings;
- 1,000-episode stability simulation;
- duplicate-lock protection;
- no-busy-spin controller guard.

Status: implemented.

## M7 — Release Hardening

- stdlib-only dependency gate;
- no `requirements.txt` or setuptools package manifest;
- direct Win32 keyboard/mouse hooks through `ctypes`;
- direct Win32 tray/notification backend through `ctypes`;
- pip-free source execution;
- pip-free CI and release workflows;
- stdlib `zipapp` release artifact;
- SHA-256 checksum generation;
- per-user startup isolation tests;
- threat model and install/upgrade/remove documentation;
- interactive real-Windows validation checklist.

Status: repository implementation complete; interactive physical Windows
keyboard/mouse, tray, multi-user, and power/suspend-resume release-candidate checks
remain external validation evidence.

## Dependency boundary

Allowed:

- Python 3.11+ standard library;
- Windows APIs supplied by the operating system;
- repository-owned source.

Not allowed:

- pip runtime dependencies;
- package-installed keyboard/mouse hooks;
- package-installed tray/UI frameworks;
- third-party frozen-app packagers;
- hidden hosted services.
