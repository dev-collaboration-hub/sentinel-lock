import unittest

from sentinel_lock.startup import (
    VALUE_NAME,
    build_startup_command,
    install_startup,
    remove_startup,
    startup_command,
)


class FakeKey:
    def __init__(self, registry: "FakeRegistry") -> None:
        self.registry = registry

    def __enter__(self) -> "FakeKey":
        return self

    def __exit__(self, *_args: object) -> None:
        return None


class FakeRegistry:
    HKEY_CURRENT_USER = object()
    REG_SZ = 1
    KEY_SET_VALUE = 2

    def __init__(self) -> None:
        self.values: dict[str, tuple[str, int]] = {}

    def CreateKey(self, _root: object, _path: str) -> FakeKey:
        return FakeKey(self)

    def OpenKey(self, _root: object, _path: str, *_args: object) -> FakeKey:
        if not self.values:
            raise FileNotFoundError
        return FakeKey(self)

    def SetValueEx(
        self,
        _key: FakeKey,
        name: str,
        _reserved: int,
        value_type: int,
        value: str,
    ) -> None:
        self.values[name] = (value, value_type)

    def QueryValueEx(self, _key: FakeKey, name: str) -> tuple[str, int]:
        if name not in self.values:
            raise FileNotFoundError
        return self.values[name]

    def DeleteValue(self, _key: FakeKey, name: str) -> None:
        if name not in self.values:
            raise FileNotFoundError
        del self.values[name]


class StartupTests(unittest.TestCase):
    def test_command_is_quoted_and_preserves_runtime_options(self) -> None:
        command = build_startup_command(["--config", "C:\\A Folder\\config.toml", "--no-tray"])
        self.assertIn("-m sentinel_lock", command)
        self.assertIn('"C:\\A Folder\\config.toml"', command)
        self.assertIn("--no-tray", command)

    def test_install_read_and_remove_round_trip(self) -> None:
        registry = FakeRegistry()
        installed = install_startup("sentinel-lock --no-tray", registry=registry)
        self.assertEqual(installed, "sentinel-lock --no-tray")
        self.assertEqual(startup_command(registry=registry), installed)
        self.assertIn(VALUE_NAME, registry.values)
        self.assertTrue(remove_startup(registry=registry))
        self.assertIsNone(startup_command(registry=registry))
        self.assertFalse(remove_startup(registry=registry))


if __name__ == "__main__":
    unittest.main()
