from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from sentinel_lock.config import ConfigError, apply_overrides, load_config


class ConfigurationTests(unittest.TestCase):
    def test_built_in_defaults_are_valid(self) -> None:
        config = load_config()

        self.assertEqual(config.security.idle_timeout_seconds, 300.0)
        self.assertEqual(config.runtime.poll_interval_seconds, 1.0)
        self.assertEqual(config.logging.level, "INFO")

    def test_loads_complete_toml_file(self) -> None:
        with TemporaryDirectory() as directory:
            path = Path(directory) / "sentinel.toml"
            path.write_text(
                """
[security]
idle_timeout_seconds = 900
[runtime]
poll_interval_seconds = 2.5
[logging]
level = "warning"
file = ""
max_bytes = 2048
backup_count = 0
""",
                encoding="utf-8",
            )

            config = load_config(path)

        self.assertEqual(config.security.idle_timeout_seconds, 900.0)
        self.assertEqual(config.runtime.poll_interval_seconds, 2.5)
        self.assertEqual(config.logging.level, "WARNING")
        self.assertIsNone(config.logging.file)
        self.assertEqual(config.logging.max_bytes, 2048)

    def test_rejects_missing_file(self) -> None:
        with self.assertRaisesRegex(ConfigError, "not found"):
            load_config("does-not-exist.toml")

    def test_rejects_unknown_key(self) -> None:
        with TemporaryDirectory() as directory:
            path = Path(directory) / "sentinel.toml"
            path.write_text(
                "[security]\ntimeout_typo = 10\n",
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ConfigError, "unknown configuration key"):
                load_config(path)

    def test_rejects_boolean_as_numeric_value(self) -> None:
        with TemporaryDirectory() as directory:
            path = Path(directory) / "sentinel.toml"
            path.write_text(
                "[security]\nidle_timeout_seconds = true\n",
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ConfigError, "must be a number"):
                load_config(path)

    def test_rejects_out_of_range_timeout(self) -> None:
        with TemporaryDirectory() as directory:
            path = Path(directory) / "sentinel.toml"
            path.write_text(
                "[security]\nidle_timeout_seconds = 1\n",
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ConfigError, "between 5 and 86400"):
                load_config(path)

    def test_command_line_overrides_create_validated_copy(self) -> None:
        original = load_config()

        updated = apply_overrides(
            original,
            idle_timeout_seconds=30,
            poll_interval_seconds=0.5,
        )

        self.assertEqual(original.security.idle_timeout_seconds, 300.0)
        self.assertEqual(updated.security.idle_timeout_seconds, 30.0)
        self.assertEqual(updated.runtime.poll_interval_seconds, 0.5)


if __name__ == "__main__":
    unittest.main()
