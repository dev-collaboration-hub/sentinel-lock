# Install, Upgrade, and Remove

Sentinel Lock does not use pip installation.

## Run from source

Requirements:

- Windows 10/11;
- Python 3.11+.

From the repository root:

```powershell
python .\run_sentinel_lock.py --check-config
python .\run_sentinel_lock.py
```

No virtual environment or package installation is required.

## Run from the stdlib release artifact

Build or download `sentinel-lock.pyz`, then:

```powershell
python .\sentinel-lock.pyz --check-config
python .\sentinel-lock.pyz
```

The `.pyz` requires Python 3.11+ on the target system.

## Automatic startup

From source:

```powershell
python .\run_sentinel_lock.py --install-startup
python .\run_sentinel_lock.py --startup-status
```

From a `.pyz` release:

```powershell
python .\sentinel-lock.pyz --install-startup
python .\sentinel-lock.pyz --startup-status
```

Startup registration is per-user under `HKEY_CURRENT_USER`.

## Upgrade source checkout

1. Stop Sentinel Lock.
2. Update the repository files.
3. Run the stdlib dependency gate and config check:

```powershell
python tests\check_stdlib_only.py
python .\run_sentinel_lock.py --check-config
```

4. If the repository path moved, refresh the per-user startup registration.

## Upgrade `.pyz`

1. Stop Sentinel Lock.
2. Verify the new release SHA-256 checksum.
3. Replace the old `.pyz` with the new artifact.
4. Run `--check-config`.
5. If the artifact path changed, remove and reinstall startup registration.

## Remove

Remove startup registration first:

```powershell
python .\run_sentinel_lock.py --remove-startup
```

or, for a release artifact:

```powershell
python .\sentinel-lock.pyz --remove-startup
```

Then delete the source checkout or `.pyz` file. There is no pip package to
uninstall. User-created config and log files are not deleted automatically.
