# Configuration

Sentinel Lock reads an optional TOML file. If `--config` is omitted, built-in
defaults are used. A missing path supplied explicitly is an error.

## Reference

### `[security]`

| Key | Type | Default | Valid range |
| --- | --- | ---: | --- |
| `idle_timeout_seconds` | number | `300` | `5` to `86400` |

The timeout is measured using a monotonic clock and starts when the application
starts or when the latest input event is received.

### `[runtime]`

| Key | Type | Default | Valid range |
| --- | --- | ---: | --- |
| `poll_interval_seconds` | number | `1.0` | `0.1` to `60` |

A smaller interval reacts closer to the exact timeout but wakes the process
more frequently. One second is appropriate for normal desktop use.

### `[logging]`

| Key | Type | Default | Valid range |
| --- | --- | --- | --- |
| `level` | string | `INFO` | `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL` |
| `file` | string or empty | `logs/sentinel-lock.log` | local file path |
| `max_bytes` | integer | `1048576` | `1024` to `104857600` |
| `backup_count` | integer | `3` | `0` to `20` |

Set `file = ""` to log to the console only.

## Command-line overrides

```powershell
sentinel-lock --config config/default.toml --timeout 900
sentinel-lock --poll-interval 2
sentinel-lock --dry-run
sentinel-lock --check-config
```

`--timeout` and `--poll-interval` use the same range validation as TOML values.
`--dry-run` replaces the native Windows locker with a log-only implementation.
`--check-config` validates the effective configuration and exits.

## Operational recommendations

- Start with a five-minute timeout on a personal workstation.
- Use a longer timeout before presentations or accessibility workflows.
- Validate changes with `--check-config`.
- Exercise the complete timing flow with `--dry-run` before enabling locking.
- Keep the log file in a user-writable directory.
