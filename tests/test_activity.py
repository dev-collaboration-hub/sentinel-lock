from datetime import datetime, timezone
from threading import Thread
import unittest

from sentinel_lock.activity import ActivityKind, ActivityManager
from tests.helpers import FakeClock


class ActivityManagerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.clock = FakeClock(100.0)
        self.wall_time = datetime(2026, 7, 30, tzinfo=timezone.utc)
        self.manager = ActivityManager(
            clock=self.clock,
            wall_clock=lambda: self.wall_time,
        )

    def test_initial_state_starts_active_without_an_event(self) -> None:
        snapshot = self.manager.snapshot()

        self.assertEqual(snapshot.sequence, 0)
        self.assertIsNone(snapshot.last_kind)
        self.assertEqual(snapshot.last_activity_monotonic, 100.0)
        self.assertEqual(snapshot.idle_seconds(102.5), 2.5)

    def test_record_updates_category_time_and_sequence(self) -> None:
        self.clock.advance(3.0)

        snapshot = self.manager.record(ActivityKind.KEYBOARD)

        self.assertEqual(snapshot.sequence, 1)
        self.assertEqual(snapshot.last_kind, ActivityKind.KEYBOARD)
        self.assertEqual(snapshot.last_activity_monotonic, 103.0)
        self.assertEqual(self.manager.idle_seconds(), 0.0)

    def test_idle_time_never_becomes_negative(self) -> None:
        snapshot = self.manager.snapshot()

        self.assertEqual(snapshot.idle_seconds(90.0), 0.0)

    def test_rejects_untyped_activity_categories(self) -> None:
        with self.assertRaises(TypeError):
            self.manager.record("keyboard")  # type: ignore[arg-type]

    def test_concurrent_updates_preserve_every_sequence(self) -> None:
        updates_per_thread = 500

        def update() -> None:
            for _ in range(updates_per_thread):
                self.manager.record(ActivityKind.MOUSE_MOVE)

        threads = [Thread(target=update) for _ in range(4)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        self.assertEqual(self.manager.snapshot().sequence, updates_per_thread * 4)


if __name__ == "__main__":
    unittest.main()
