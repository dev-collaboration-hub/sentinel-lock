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

- distinguish meaningful mouse activity from tiny accidental movement/noise;
- preserve immediate keyboard and mouse-click activity updates;
- keep activity classification deterministic and lightweight;
- avoid storing raw keys, mouse buttons, or pointer coordinates;
- add deterministic tests for movement filtering and activity refresh behavior;
- document the exact threshold/rules used for meaningful mouse movement.

Status: planned.

## M5 — Runtime Experience

- system tray controls;
- desktop notifications;
- optional Windows startup registration;
- suspend and resume handling;
- clear idle and lock status without exposing private input data.

Status: planned.

## M6 — Reliability and Performance

- high-frequency keyboard and mouse stress testing;
- listener recovery after transient input-hook failure;
- bounded CPU and memory benchmarks;
- long-running stability tests;
- protection against duplicate lock requests;
- validation that movement filtering remains lightweight.

Status: planned.

## M7 — Release Hardening

- signed Windows packaging;
- multi-user validation;
- accessibility and power-consumption testing;
- threat-model review;
- installation, upgrade, and removal documentation;
- stable v1.0 release.

Status: planned.
