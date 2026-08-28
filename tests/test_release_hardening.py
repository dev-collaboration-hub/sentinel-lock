import unittest

from sentinel_lock.idle import IdleLockController
from sentinel_lock.startup import RUN_KEY, VALUE_NAME, install_startup, remove_startup, startup_command
from tests.helpers import FakeClock, RecordingLocker
from sentinel_lock.activity import ActivityManager


class FakeKey:
    def __init__(self, registry: "PerUserRegistry") -> None:
        self.registry = registry

    def __enter__(self) -> "FakeKey":
        return self

    def __exit__(self, *_args: object) -> None:
        return None


class PerUserRegistry:
    HKEY_CURRENT_USER = object()
    REG_SZ = 1
    KEY_SET_VALUE = 2

    def __init__(self) -> None:
        self.values: dict[str, tuple[str, int]] = {}
        self.roots: list[object] = []
        self.paths: list[str] = []

    def CreateKey(self, root: object, path: str) -> FakeKey:
        self.roots.append(root)
        self.paths.append(path)
        return FakeKey(self)

    def OpenKey(self, root: object, path: str, *_args: object) -> FakeKey:
        self.roots.append(root)
        self.paths.append(path)
        if not self.values:
            raise FileNotFoundError
        return FakeKey(self)

    def SetValueEx(self, _key: FakeKey, name: str, _reserved: int, value_type: int, value: str) -> None:
        self.values[name] = (value, value_type)

    def QueryValueEx(self, _key: FakeKey, name: str) -> tuple[str, int]:
        if name not in self.values:
            raise FileNotFoundError
        return self.values[name]

    def DeleteValue(self, _key: FakeKey, name: str) -> None:
        if name not in self.values:
            raise FileNotFoundError
        del self.values[name]


class WaitOnceEvent:
    def __init__(self) -> None:
        self.wait_calls: list[float] = []
        self.stopped = False

    def is_set(self) -> bool:
        return self.stopped

    def wait(self, timeout: float) -> bool:
        self.wait_calls.append(timeout)
        self.stopped = True
        return True


class ReleaseHardeningTests(unittest.TestCase):
    def test_startup_registration_is_per_user_and_isolated(self) -> None:
        user_a = PerUserRegistry()
        user_b = PerUserRegistry()

        install_startup("sentinel-lock --no-tray", registry=user_a)
        install_startup("sentinel-lock --timeout 30", registry=user_b)

        self.assertEqual(startup_command(registry=user_a), "sentinel-lock --no-tray")
        self.assertEqual(startup_command(registry=user_b), "sentinel-lock --timeout 30")
        self.assertTrue(remove_startup(registry=user_a))
        self.assertIsNone(startup_command(registry=user_a))
        self.assertEqual(startup_command(registry=user_b), "sentinel-lock --timeout 30")
        self.assertTrue(all(root is user_a.HKEY_CURRENT_USER for root in user_a.roots))
        self.assertTrue(all(root is user_b.HKEY_CURRENT_USER for root in user_b.roots))
        self.assertTrue(all(path == RUN_KEY for path in user_a.paths + user_b.paths))
        self.assertIn(VALUE_NAME, user_b.values)

    def test_controller_waits_between_polls_instead_of_busy_spinning(self) -> None:
        clock = FakeClock()
        manager = ActivityManager(clock=clock)
        controller = IdleLockController(
            manager,
            RecordingLocker(),
            idle_timeout_seconds=30,
            poll_interval_seconds=2.5,
            clock=clock,
        )
        stop_event = WaitOnceEvent()

        controller.run(stop_event)  # type: ignore[arg-type]

        self.assertEqual(stop_event.wait_calls, [2.5])


if __name__ == "__main__":
    unittest.main()
