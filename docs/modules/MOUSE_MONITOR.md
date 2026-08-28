# Mouse Monitor Module

## Native input source

`MouseMonitor` receives occurrence callbacks from the repository-owned
`Win32MouseListener` in `src/sentinel_lock/win32_input.py`.

The listener installs `WH_MOUSE_LL` with `SetWindowsHookExW` through Python
`ctypes`. It does **not** dereference `MSLLHOOKSTRUCT`, so real pointer coordinates
and mouse-button identity never enter Sentinel Lock.

For compatibility with the monitor callback boundary it emits placeholder
`(0, 0)` coordinates and `None` button identity; `MouseMonitor` ignores those
values.

## M4 meaningful movement rule

1. one movement occurrence starts a candidate burst;
2. a second movement occurrence within **250 ms** confirms meaningful movement;
3. the burst refreshes activity as `MOUSE_MOVE`;
4. continuous movement refresh is limited to once every **500 ms**;
5. a gap longer than 250 ms starts a new candidate burst.

The filter stores only monotonic timing state.

## Click and keyboard behavior

- mouse button-down occurrence refreshes activity immediately;
- button identity is discarded by the native hook adapter;
- a click resets pending movement state;
- keyboard key-down occurrence refreshes immediately;
- keyboard hook payloads are not dereferenced.

## Deterministic constants

| Rule | Value |
| --- | ---: |
| Movement confirmation window | 0.25 seconds |
| Continuous movement refresh interval | 0.50 seconds |
| Required callbacks for initial confirmation | 2 |

## Verification

`tests/test_monitors.py` verifies filtering and privacy state with fake listeners.
On Windows, `tests/test_win32_native.py` verifies that the repository-owned native
adapter maps Win32 messages to occurrence callbacks without payload content.

A physical mouse/interactive desktop smoke test remains release-candidate evidence
because hosted CI does not prove a human-operated Windows desktop hook session.
