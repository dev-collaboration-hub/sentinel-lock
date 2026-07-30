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

## Adding a new signal provider

Presence and device-proximity providers should implement their own adapter and
publish minimal state to a future decision engine. A provider must define:

1. its local data source;
2. data-retention rules;
3. error and unavailable states;
4. sampling and CPU limits;
5. deterministic tests with no hardware dependency.
