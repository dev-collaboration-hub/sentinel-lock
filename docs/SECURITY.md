# Security and Privacy Model

## Protected scenario

Sentinel Lock reduces the window in which a logged-in Windows session remains
available after its user stops interacting with the keyboard and mouse.

It is a defense-in-depth control. It does not replace a strong Windows password,
full-disk encryption, operating-system updates, or physical security.

## Privacy guarantees

The application does not intentionally store or transmit:

- key values or typed text;
- mouse buttons or pointer coordinates;
- clipboard data;
- application names, document contents, or browsing history.

Input adapters translate all callbacks into one of three categories:
`keyboard`, `mouse_move`, or `mouse_click`. Only the most recent monotonic event
time, wall-clock observation time, category, and sequence counter are kept in
memory.

Sentinel Lock has no network component and no telemetry.

## Trust boundaries

- `pynput` receives local input callbacks from the operating system.
- the in-process activity manager is trusted to serialize state updates;
- the controller decides when policy requires a lock;
- `user32!LockWorkStation` is trusted to hand control to Windows.

Configuration and log paths are local trust boundaries. Run Sentinel Lock as a
normal user, protect its configuration from untrusted modification, and do not
run it from an untrusted working directory.

## Failure behavior

- Invalid configuration prevents startup.
- Failure to start any required input monitor prevents the controller from
  running.
- A failed native lock request is logged as an error and can be retried.
- A successful request is emitted once for that idle episode.
- Listener shutdown is bounded so service termination cannot wait forever.

## Known limitations

- The MVP targets Windows 10 and Windows 11.
- Input monitoring depends on the privileges and desktop session available to
  `pynput`.
- System suspend and resume behavior should be validated on each target device.
- Malware or an administrator can stop or alter a user-level process.

## Reporting a vulnerability

Do not disclose exploitable details in a public issue. Contact the repository
maintainers privately through the GitHub organization security channel. Include
the affected version, reproduction conditions, and expected impact without
including real passwords, typed content, or personal data.
