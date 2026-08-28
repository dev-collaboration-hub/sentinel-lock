# M6 Reliability and Performance

M6 strengthens the existing keyboard/mouse-only runtime without adding new
activity sources, telemetry, remote services, or private input retention.

## Runtime recovery

`MonitorSupervisor` polls input-monitor health from the controller's normal
runtime maintenance cycle.

For the built-in keyboard and mouse monitors:

1. the underlying `pynput` listener is probed with `is_alive()`;
2. a stopped listener is replaced through `restart()`;
3. a transient restart failure is logged and may be retried on the next poll;
4. mouse recovery clears pending movement-filter timing state before listening
   again;
5. raw keys, mouse buttons, and pointer coordinates are never part of recovery
   state.

Custom monitors that do not expose both `is_alive()` and `restart()` are left
untouched by the supervisor.

## CI performance guards

The M6 test suite uses deterministic, local standard-library measurements. The
guards are intentionally generous enough to avoid runner noise while still
catching accidental unbounded work or allocation growth.

### Keyboard stress

- 10,000 keyboard callbacks per test;
- every callback must be accepted as activity;
- process CPU time must stay below 10 seconds;
- Python traced peak memory must stay below 32 MiB.

### Mouse movement stress

- 10,000 movement callbacks with a deterministic fake clock;
- the M4 timing filter must keep refreshes bounded rather than recording every
  callback;
- process CPU time must stay below 10 seconds;
- Python traced peak memory must stay below 32 MiB.

These are regression ceilings, not claims about end-user benchmark numbers.
Hardware-specific CPU and memory measurements may be lower or higher depending
on Windows version, Python build, input-hook backend, and machine load.

## Long-run stability simulation

The test suite simulates 1,000 complete idle episodes. Each episode:

1. reaches the idle threshold;
2. requests exactly one lock;
3. performs repeated duplicate evaluations while still idle;
4. records new keyboard activity;
5. rearms for the next episode.

The final lock-call count must equal the number of idle episodes exactly.
Repeated runtime `Lock now` requests during an already-locked episode are also
verified not to bypass the one-lock-per-episode guard.

## Failure boundaries

- listener health-probe exceptions are treated as unhealthy state;
- listener restart failures are logged without crashing the controller loop;
- native workstation-lock failures retain the existing retry behavior;
- runtime maintenance failures are isolated from idle evaluation;
- no recovery feature changes the keyboard/mouse-only activity policy.

## Evidence command

```powershell
python -m unittest discover -s tests -v
python -m compileall -q src tests
```

M6 is complete only when the repository's GitHub Actions matrix passes these
checks on Windows and Ubuntu for every supported Python version in CI.
