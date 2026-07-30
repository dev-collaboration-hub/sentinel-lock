import unittest

from sentinel_lock.activity import ActivityKind, ActivityManager
from sentinel_lock.monitors import KeyboardMonitor, MonitorStartError, MouseMonitor
from tests.helpers import FakeClock, FakeListener


class MonitorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.clock = FakeClock()
        self.manager = ActivityManager(clock=self.clock)

    def test_keyboard_press_updates_activity_without_retaining_key(self) -> None:
        listener = FakeListener()

        def factory(**callbacks: object) -> FakeListener:
            listener.callbacks = callbacks
            return listener

        monitor = KeyboardMonitor(self.manager, listener_factory=factory)
        monitor.start()
        listener.callbacks["on_press"]("secret-value")

        snapshot = self.manager.snapshot()
        self.assertTrue(listener.started)
        self.assertEqual(snapshot.last_kind, ActivityKind.KEYBOARD)
        self.assertFalse(hasattr(snapshot, "key"))

        monitor.stop()
        monitor.join(2.0)
        self.assertTrue(listener.stopped)
        self.assertEqual(listener.join_timeout, 2.0)

    def test_mouse_move_and_pressed_click_are_distinct_events(self) -> None:
        listener = FakeListener()

        def factory(**callbacks: object) -> FakeListener:
            listener.callbacks = callbacks
            return listener

        monitor = MouseMonitor(self.manager, listener_factory=factory)
        monitor.start()
        listener.callbacks["on_move"](50, 70)
        listener.callbacks["on_click"](50, 70, "left", False)
        listener.callbacks["on_click"](50, 70, "left", True)

        snapshot = self.manager.snapshot()
        self.assertEqual(snapshot.sequence, 2)
        self.assertEqual(snapshot.last_kind, ActivityKind.MOUSE_CLICK)
        self.assertFalse(hasattr(snapshot, "coordinates"))

    def test_start_is_idempotent(self) -> None:
        calls = 0

        def factory(**callbacks: object) -> FakeListener:
            nonlocal calls
            calls += 1
            return FakeListener(**callbacks)

        monitor = KeyboardMonitor(self.manager, listener_factory=factory)
        monitor.start()
        monitor.start()

        self.assertEqual(calls, 1)

    def test_listener_start_failure_is_clear(self) -> None:
        class BrokenListener(FakeListener):
            def start(self) -> None:
                raise RuntimeError("backend unavailable")

        monitor = KeyboardMonitor(
            self.manager,
            listener_factory=lambda **callbacks: BrokenListener(**callbacks),
        )

        with self.assertRaisesRegex(MonitorStartError, "backend unavailable"):
            monitor.start()


if __name__ == "__main__":
    unittest.main()
