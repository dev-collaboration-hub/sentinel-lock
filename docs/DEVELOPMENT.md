# Development Guide

## Environment

Sentinel Lock supports Python 3.11+ and uses no pip packages.

Run directly from the repository root:

```powershell
python .\run_sentinel_lock.py --version
```

No virtual environment or package installation is required.

## Validation

Run before every change:

```powershell
python tests\check_stdlib_only.py
$env:PYTHONPATH = "src"
python -m unittest discover -s tests -v
python -m compileall -q src tests run_sentinel_lock.py
```

Manual Windows smoke test:

```powershell
python .\run_sentinel_lock.py --check-config
python .\run_sentinel_lock.py --dry-run --timeout 10
python .\run_sentinel_lock.py --timeout 10
```

The final command can lock the active workstation.

## Design rules

- Python standard library + Windows system APIs only.
- No pip/runtime dependencies.
- Keep input callbacks constant-time.
- Use monotonic time for durations.
- Keep Windows API access behind small adapters.
- Never retain/log key values, mouse buttons, pointer coordinates, or user content.
- Do not add network calls or telemetry.
- Raise clear startup errors when native hooks cannot start.
- Preserve deterministic tests by injecting fake listener factories where possible.

## Test strategy

The suite uses fake clocks, lockers, listener factories, registry adapters, and
runtime backends for deterministic policy tests. Windows CI additionally imports
and exercises event mapping in the repository-owned `ctypes` Win32 adapters.

Unit tests do not attach real global input hooks or call `LockWorkStation` on the
CI machine. Physical desktop hook/tray behavior remains an explicit interactive
Windows smoke test.

## Modifying native input

`win32_input.py` is the only scratch low-level hook implementation. Changes must:

1. preserve `CallNextHookEx`;
2. clean up hooks with `UnhookWindowsHookEx`;
3. retain only input occurrence, never hook payload content;
4. preserve monitor health/restart semantics;
5. keep fake-listener monitor tests working;
6. pass the stdlib-only dependency gate.
