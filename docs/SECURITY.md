# Security and Privacy Model

## Protected scenario

Sentinel Lock reduces the window in which a logged-in Windows session remains
available after its user stops interacting with the keyboard and mouse.

It is a defense-in-depth control, not an authentication replacement.

## Privacy guarantees

The application does not intentionally store or transmit:

- key values or typed text;
- mouse-button identity or pointer coordinates;
- clipboard data;
- application names, document contents, or browsing history.

The repository-owned low-level keyboard hook does not dereference the keyboard
hook structure. The mouse hook does not dereference the mouse hook structure.
Only occurrence messages are mapped to `keyboard`, `mouse_move`, or `mouse_click`.

`ActivityManager` retains only the latest monotonic timestamp, wall-clock
observation time, category, and sequence counter.

Sentinel Lock has no network component and no telemetry.

## Trust boundaries

- repository-owned `ctypes` adapters call Win32 input APIs;
- the in-process Activity Manager serializes minimal state;
- the controller decides when policy requires a lock;
- `user32!LockWorkStation` hands control to Windows;
- the native tray adapter uses Win32/Shell notification APIs;
- startup registration uses stdlib `winreg` under `HKEY_CURRENT_USER`.

There are no pip/runtime package trust boundaries.

## Failure behavior

- invalid configuration prevents startup;
- failure to install a required native input hook prevents normal runtime start;
- dead native hook threads are detected and restart is attempted;
- failed native lock requests are logged and can be retried;
- successful automatic lock requests occur once per idle episode;
- listener and tray shutdown waits are bounded.

## Known limitations

- Windows 10 and Windows 11 are the runtime target;
- low-level hook behavior depends on the current user's interactive desktop and
  Windows integrity/privilege rules;
- physical input, tray, accessibility, and suspend/resume behavior still require
  interactive Windows release-candidate validation;
- malware or an administrator can stop or alter a user-level process;
- the stdlib `.pyz` release requires a trusted Python 3.11+ installation.

## Reporting a vulnerability

Do not disclose exploitable details in a public issue. Contact the repository
maintainers privately through the GitHub organization security channel. Do not
include real passwords, typed content, or personal data in reports.
