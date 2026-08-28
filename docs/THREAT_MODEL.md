# Threat Model

## Protected asset

Sentinel Lock reduces the chance that an unattended Windows session stays usable after keyboard and mouse inactivity.

## Trust boundary

The core accepts only local keyboard presses, meaningful mouse movement, and mouse clicks. Camera, microphone, Bluetooth, network presence, location, and remote policy sources are outside the repository boundary.

## Threats considered

- accidental unattended-session exposure;
- mouse sensor jitter preventing an idle lock;
- transient keyboard or mouse hook failure;
- duplicate lock requests during one idle episode;
- raw key, mouse button, or pointer-coordinate retention;
- startup registration escaping the current Windows user;
- unsigned or tampered release artifacts;
- runtime UI bypassing the controller and calling platform lock APIs directly.

## Mitigations

- deterministic idle threshold and one-lock-per-episode guard;
- timing-only movement confirmation and rate limiting;
- monitor health probing with bounded restart attempts on later polls;
- raw input values discarded at callback boundaries;
- startup uses `HKEY_CURRENT_USER` only;
- tray `Lock now` queues a controller request rather than calling Windows APIs;
- tagged release workflow refuses to publish without production signing secrets;
- tagged Windows executable must pass Authenticode validation before publication;
- release artifacts include SHA-256 checksums.

## Explicit non-goals

Sentinel Lock is not an authentication replacement, malware defense, anti-tamper kernel component, remote device-management agent, or biometric presence detector. An attacker already controlling the user account or process can terminate or modify a user-space utility.

## Residual risks

Input hooks, tray behavior, Windows power transitions, Authenticode trust chains, accessibility behavior, and multi-user startup semantics depend on the real Windows environment. These require release-candidate validation on physical/interactive Windows systems in addition to CI.
