# Mouse Monitor Module

## M4 behavior

`MouseMonitor` keeps Sentinel Lock keyboard/mouse-only while filtering isolated
pointer jitter without retaining pointer coordinates.

### Meaningful movement rule

Mouse movement is considered meaningful when:

1. one movement callback starts a candidate movement burst;
2. a second movement callback arrives within **250 ms**;
3. the confirmed burst refreshes activity as `MOUSE_MOVE`;
4. while movement continues, activity refresh is limited to at most once every
   **500 ms**;
5. a gap longer than 250 ms resets the candidate burst, so a new isolated move
   does not refresh activity by itself.

The filter is deterministic and based only on monotonic callback timing. The
`x` and `y` values supplied by `pynput` are ignored immediately and are never
stored, logged, or sent elsewhere.

### Click and keyboard behavior

- A pressed mouse click refreshes activity immediately.
- Mouse-button release callbacks do not refresh activity.
- A pressed click resets any pending movement burst.
- Keyboard presses continue to refresh activity immediately.

## Why timing instead of pointer distance

Distance-based filtering would require retaining at least a previous pointer
position. M4 deliberately avoids that privacy cost. Timing-based burst
confirmation removes one-off jitter while preserving the existing rule that raw
pointer coordinates are not retained.

## Deterministic constants

| Rule | Value |
| --- | ---: |
| Movement confirmation window | 0.25 seconds |
| Continuous movement refresh interval | 0.50 seconds |
| Required callbacks for initial confirmation | 2 |

These constants live in `src/sentinel_lock/monitors/mouse.py` and are covered by
unit tests.

## M4 verification

`tests/test_monitors.py` verifies:

- one isolated movement callback is ignored;
- two callbacks inside the confirmation window refresh activity;
- a movement gap beyond the confirmation window resets the burst;
- continuous movement refresh is rate-limited;
- pressed clicks remain immediate;
- release callbacks remain ignored;
- coordinate values are not added to activity state.

M4 is complete only when the repository unit tests and Python compilation checks
pass on the supported CI matrix.
