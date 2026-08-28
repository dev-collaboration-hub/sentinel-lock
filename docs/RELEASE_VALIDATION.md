# M7 Release Validation

Sentinel Lock now uses a stdlib-only distribution model. There is no PyInstaller
or pip-installed release toolchain.

## Automated CI gates

- stdlib-only dependency gate on Windows and Ubuntu;
- full unit-test suite on Windows and Ubuntu, Python 3.11 and 3.12;
- source compilation;
- no-install source-launcher smoke test;
- stdlib `zipapp` build on Windows;
- `.pyz --version` smoke test;
- SHA-256 checksum generation.

## Distribution boundary

The release artifact is `sentinel-lock.pyz`. It contains repository Python source
and requires Python 3.11+ on the target Windows system.

The project deliberately does not freeze or bundle a third-party Python runtime,
so Authenticode executable signing is no longer a release gate for the `.pyz`
artifact. SHA-256 checksum verification remains required.

## Multi-user validation

Use two standard Windows user accounts. For each account:

1. run Sentinel Lock from the same source or `.pyz` release;
2. install startup registration;
3. confirm the other account's startup entry is unchanged;
4. remove startup registration;
5. confirm only the current user's entry was removed.

Deterministic tests already verify independent `HKEY_CURRENT_USER` stores. Real
account switching remains an interactive release-candidate check.

## Native input validation

On a real interactive Windows desktop confirm:

- keyboard presses refresh activity;
- isolated mouse movement is filtered according to M4 rules;
- sustained mouse movement refreshes activity;
- pressed clicks refresh immediately;
- raw keys, button identity, and coordinates are not logged;
- stopping/restarting a hook recovers without duplicate activity.

GitHub-hosted Windows CI validates the ctypes adapter import/event mapping, but it
is not treated as proof of a user's physical keyboard/mouse desktop session.

## Accessibility validation

- tray status is text-based;
- Lock now and Exit have explicit labels;
- `--no-tray` supports foreground/headless operation;
- notifications can be disabled with `--no-notifications`.

## Power / suspend-resume validation

Repository tests enforce bounded CPU/memory regression ceilings and prove the
controller waits between polls rather than busy-spinning. A real Windows release
candidate still needs an extended active/idle/sleep/resume smoke test.

## Stable release gate

Do not call a release fully interactive-Windows-verified until these are recorded:

- 4/4 test matrix green;
- stdlib dependency gate green;
- zipapp build/smoke/checksum green;
- two-user startup validation;
- real keyboard/mouse hook validation;
- tray/accessibility check;
- power/suspend/resume check;
- source or `.pyz` upgrade/remove smoke test.
