# Threat Model

## Protected asset

Sentinel Lock reduces the chance that an unattended Windows session remains
usable after keyboard and mouse inactivity.

## Trust boundary

The core accepts only local keyboard press occurrence, meaningful mouse movement
occurrence, and mouse click occurrence. Camera, microphone, Bluetooth, network
presence, location, and remote policy sources are outside the repository boundary.

## Threats considered

- unattended-session exposure;
- mouse sensor jitter preventing idle lock;
- transient keyboard/mouse hook failure;
- duplicate lock requests during one idle episode;
- raw key/button/coordinate retention;
- startup registration escaping the current Windows user;
- tampered release artifact;
- runtime UI bypassing the controller;
- reintroduction of third-party runtime dependencies.

## Mitigations

- deterministic idle threshold and one-lock-per-episode guard;
- timing-only movement confirmation/rate limiting;
- repository-owned low-level Win32 hooks;
- hook payload structures are not dereferenced;
- monitor health probing and restart;
- startup uses `HKEY_CURRENT_USER` only;
- tray Lock now queues a controller request;
- SHA-256 checksum for the stdlib `.pyz` release artifact;
- CI parses application imports and rejects non-stdlib dependency roots;
- CI/release workflows reject pip-install and former third-party packager paths.

## Explicit non-goals

Sentinel Lock is not an authentication replacement, malware defense, anti-tamper
kernel component, remote device-management agent, biometric presence detector, or
raw NT syscall project. It is a user-space Win32 utility implemented through
Python standard-library `ctypes`.

## Residual risks

Low-level hooks, tray behavior, Windows power transitions, accessibility behavior,
and real multi-user startup semantics depend on an interactive Windows
environment. The `.pyz` artifact also depends on the integrity of the installed
Python interpreter. These require release-candidate validation beyond hosted CI.
