# Roadmap

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
- recovery after new activity;
- native `LockWorkStation` adapter;
- dry-run safety mode;
- deterministic threshold and failure tests.

Status: implemented.

## M3 — Adaptive Lock Foundation

- keep idle locking as the safe baseline;
- accept optional local `user_present` signal;
- accept optional local `trusted_device_nearby` signal;
- use one small lock decision path;
- preserve baseline behavior when optional signals fail or are unavailable.

Status: implemented.

## M4 — Local Presence Signals

- computer-vision presence adapter;
- optional local face-recognition adapter;
- Bluetooth phone proximity adapter;
- trusted-device adapter;
- privacy rules for every signal source;
- deterministic adapter tests.

Status: planned. Each adapter should only return simple local state to the
existing lock controller.

## M5 — Runtime Experience

- system tray controls;
- desktop notifications;
- optional Windows startup registration;
- suspend and resume handling;
- clear signal and lock status without exposing private input data.

Status: planned.

## M6 — Reliability and Performance

- high-frequency input stress testing;
- listener recovery after transient input-hook failure;
- bounded CPU and memory benchmarks;
- long-running stability tests;
- multi-signal failure handling;
- protection against duplicate lock requests.

Status: planned.

## M7 — Release Hardening

- signed Windows packaging;
- multi-user validation;
- accessibility and power-consumption testing;
- threat-model review;
- installation, upgrade, and removal documentation;
- stable v1.0 release;
- evaluate cross-platform adapters without complicating the Windows core.

Status: planned.
