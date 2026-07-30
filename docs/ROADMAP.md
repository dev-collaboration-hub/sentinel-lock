# Roadmap

## M1 — Activity Monitoring

- keyboard press activity;
- mouse movement activity;
- mouse click activity;
- thread-safe centralized activity state;
- listener lifecycle and deterministic tests.

Status: implemented in the initial MVP.

## M2 — Idle Detection Engine

- configurable monotonic idle timer;
- one lock decision per idle episode;
- recovery after new activity;
- deterministic threshold and failure tests.

Status: implemented in the initial MVP.

## M3 — Windows Lock Integration

- native `LockWorkStation` adapter;
- platform validation;
- dry-run safety mode;
- clear native failure reporting.

Status: implemented in the initial MVP.

## M4 — Runtime Operations

- validated TOML configuration;
- command-line overrides;
- privacy-safe rotating logs;
- graceful startup and shutdown;
- optional Windows startup registration and system tray controls.

Status: core runtime implemented; startup registration and tray controls remain.

## M5 — Presence-Aware Decisions

- local-only human-presence provider;
- optional authorized-user verification;
- optional trusted Bluetooth device proximity;
- explicit unknown/unavailable signal states;
- confidence policy designed to avoid false locks;
- privacy and performance evaluation.

Status: planned.

## M6 — Release Hardening

- signed Windows packaging;
- suspend/resume and multi-user validation;
- accessibility and power-consumption testing;
- threat-model review;
- installation, upgrade, and removal documentation;
- stable v1.0 release.

Status: planned.
