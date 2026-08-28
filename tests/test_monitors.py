import unittest

from sentinel_lock.activity import ActivityKind, ActivityManager
from sentinel_lock.monitors import KeyboardMonitor, MonitorStartError, MouseMonitor
from tests.helpers import FakeClock, FakeListener


class MonitorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.clock = FakeClock()
        self.manager = ActivityManager(clock=self.clock)

    def _mouse_monitor(self) -> tuple[MouseMonitor, FakeListener]:
        listener = FakeListener()

        def factory(**callbacks: object) -> FakeListener:
            listener.callbacks = callbacks
            return listener

        monitor = MouseMonitor(
            self.manager,
            listener_factory=factory,
            clock=self.clock,
        )
        monitor.start()
        return monitor, listener

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

    def test_isolated_mouse_move_is_filtered(self) -> None:
        _monitor, listener = self._mouse_monitor()
        listener.callbacks["on_move"](50, 70)

        self.assertEqual(self.manager.snapshot().sequence, 0)

        self.clock.advance(0.30)
        listener.callbacks["on_move"](51, 70)
        self.assertEqual(self.manager.snapshot().sequence, 0)

    def test_two_mouse_moves_inside_window_refresh_activity(self) -> None:
        _monitor, listener = self._mouse_monitor()
        listener.callbacks["on_move"](50, 70)
        self.clock.advance(0.10)
        listener.callbacks["on_move"](51, 71)

        snapshot = self.manager.snapshot()
        self.assertEqual(snapshot.sequence, 1)
        self.assertEqual(snapshot.last_kind, ActivityKind.MOUSE_MOVE)
        self.assertFalse(hasattr(snapshot, "coordinates"))

    def test_continuous_mouse_movement_refresh_is_rate_limited(self) -> None:
        _monitor, listener = self._mouse_monitor()
        listener.callbacks["on_move"](10, 10)
        self.clock.advance(0.10)
        listener.callbacks["on_move"](11, 10)
        self.assertEqual(self.manager.snapshot().sequence, 1)

        for point in range(4):
            self.clock.advance(0.10)
            listener.callbacks["on_move"](12 + point, 10)
        self.assertEqual(self.manager.snapshot().sequence, 1)

        self.clock.advance(0.10)
        listener.callbacks["on_move"](20, 10)
        self.assertEqual(self.manager.snapshot().sequence, 2)

    def test_pressed_click_is_immediate_and_release_is_ignored(self) -> None:
        _monitor, listener = self._mouse_monitor()
        listener.callbacks["on_click"](50, 70, "left", False)
        self.assertEqual(self.manager.snapshot().sequence, 0)

        listener.callbacks["on_click"](50, 70, "left", True)
        snapshot = self.manager.snapshot()
        self.assertEqual(snapshot.sequence, 1)
        self.assertEqual(snapshot.last_kind, ActivityKind.MOUSE_CLICK)
        self.assertFalse(hasattr(snapshot, "coordinates"))
        self.assertFalse(hasattr(snapshot, "button"))

    def test_click_resets_pending_mouse_movement_burst(self) -> None:
        _monitor, listener = self._mouse_monitor()
        listener.callbacks["on_move"](1, 1)
        self.clock.advance(0.10)
        listener.callbacks["on_click"](1, 1, "left", True)
        self.clock.advance(0.10)
        listener.callbacks["on_move"](2, 2)

        self.assertEqual(self.manager.snapshot().sequence, 1)

        self.clock.advance(0.10)
        listener.callbacks["on_move"](3, 3)
        self.assertEqual(self.manager.snapshot().sequence, 2)

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
