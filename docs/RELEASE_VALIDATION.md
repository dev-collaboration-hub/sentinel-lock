# M7 Release Validation

M7 separates deterministic repository evidence from checks that require an interactive Windows release candidate and a real code-signing identity.

## CI gates

- full unit-test suite on Windows and Ubuntu, Python 3.11 and 3.12;
- Python source compilation;
- Windows single-file executable build and `--version` smoke test;
- SHA-256 checksum generation;
- tagged releases require signing secrets;
- tagged Windows executable must report a valid Authenticode signature before publication.

## Multi-user validation

Use two standard Windows user accounts. For each account:

1. install or run Sentinel Lock;
2. install startup registration;
3. confirm the other account's startup entry is unchanged;
4. remove startup registration;
5. confirm only the current user's entry was removed.

The implementation uses `HKEY_CURRENT_USER`, and deterministic tests validate independent per-user registry stores. Real account switching remains a release-candidate check.

## Accessibility validation

On an interactive Windows desktop:

- tray status is readable as text, not color-only state;
- `Lock now` and `Exit` have explicit text labels;
- keyboard navigation/standard tray interaction remains usable with Windows accessibility settings;
- `--no-tray` allows headless/foreground operation when tray interaction is unsuitable;
- notifications are optional with `--no-notifications`.

## Power validation

Repository tests already enforce bounded CPU/memory under high event rates and the controller waits between polls instead of busy-spinning. For a release candidate, run Sentinel Lock for an extended idle/active session and compare Windows power/CPU observations against the same machine without Sentinel Lock. Record average CPU, memory, sleep/resume behavior, and whether the process prevents normal sleep.

## Production signing

A production release requires a trusted Windows code-signing certificate supplied to GitHub Actions as:

- `WINDOWS_SIGNING_CERT_BASE64`
- `WINDOWS_SIGNING_CERT_PASSWORD`

The tagged-release workflow fails closed when either secret is missing. Do not substitute an ephemeral/self-signed CI certificate as production evidence.

## Stable v1.0 gate

Do not call v1.0 release-verified until all of the following are recorded:

- 4/4 normal CI matrix green on release HEAD;
- packaged EXE smoke test green;
- trusted Authenticode signature valid;
- two-user startup validation complete;
- interactive tray/accessibility check complete;
- real Windows power/suspend/resume check complete;
- install/upgrade/remove smoke test complete.
