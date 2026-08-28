# Install, Upgrade, and Remove

## Install

PowerShell:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install .
sentinel-lock --check-config
```

For automatic start at sign-in:

```powershell
sentinel-lock --install-startup
sentinel-lock --startup-status
```

Startup registration is per-user under `HKEY_CURRENT_USER`; it does not create a machine-wide service or administrator startup entry.

## Upgrade

1. Stop Sentinel Lock from the tray or foreground terminal.
2. Record any custom config path or CLI startup options.
3. Upgrade the package:

```powershell
python -m pip install --upgrade .
```

4. Re-run config validation:

```powershell
sentinel-lock --check-config
```

5. If the Python environment or executable path changed, refresh startup registration:

```powershell
sentinel-lock --remove-startup
sentinel-lock --install-startup
sentinel-lock --startup-status
```

6. Start Sentinel Lock and verify tray status, keyboard activity, meaningful mouse movement, idle lock behavior, and resume behavior.

## Remove

Remove startup registration first:

```powershell
sentinel-lock --remove-startup
```

Then uninstall the Python package:

```powershell
python -m pip uninstall sentinel-lock
```

Optional user-created files such as custom TOML configuration or logs are not deleted automatically. Delete them manually only when no longer needed.

## Packaged EXE

For a release executable, verify the SHA-256 checksum and Windows digital signature before execution. Tagged GitHub releases are designed to publish only after the release workflow validates the Authenticode signature.
