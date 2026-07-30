# Development Guide

## Environment

Sentinel Lock supports Python 3.11 and newer. The runtime target is Windows, but
the core tests are intentionally platform-independent.

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
```

## Validation

Run before every pull request:

```powershell
python -m unittest discover -s tests -v
python -m compileall -q src tests
```

For a manual Windows smoke test:

```powershell
sentinel-lock --check-config
sentinel-lock --dry-run --timeout 10
sentinel-lock --timeout 10
```

The final command will lock the active workstation.

## Design rules

- Keep input callbacks constant-time.
- Use monotonic time for durations.
- Inject platform or timing dependencies into policy components.
- Never log key values, button values, pointer coordinates, or user content.
- Do not add network calls or telemetry.
- Raise clear startup errors when a required monitor cannot start.
- Include tests for success, boundary, and failure behavior.

## Test strategy

The suite uses:

- a controllable fake clock for deterministic idle duration;
- a recording locker for lock-attempt assertions;
- fake `pynput` listener factories for callback and lifecycle behavior;
- temporary directories for configuration and logging tests.

Unit tests must never call `LockWorkStation` or attach real keyboard/mouse hooks.

## Modifying an input monitor

The runtime supports keyboard presses, mouse movement, and mouse clicks only.
Any monitor change must:

1. publish one of the existing `ActivityKind` values;
2. discard raw key, button, and pointer data;
3. keep callbacks constant-time;
4. preserve start, stop, and bounded-join behaviour;
5. include deterministic tests with fake listeners.
