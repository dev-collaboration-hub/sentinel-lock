import logging
import unittest

from sentinel_lock.activity import ActivityKind, ActivityManager
from sentinel_lock.decision import PresenceSignals
from sentinel_lock.idle import ControllerState, IdleLockController
from tests.helpers import FakeClock, RecordingLocker


class IdleLockControllerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.clock = FakeClock()
        self.manager = ActivityManager(clock=self.clock)
        self.locker = RecordingLocker()
        self.controller = IdleLockController(
            self.manager,
            self.locker,
            idle_timeout_seconds=10,
            poll_interval_seconds=1,
            clock=self.clock,
        )

    def test_does_not_lock_before_timeout(self) -> None:
        self.clock.advance(9.9)

        evaluation = self.controller.evaluate_once()

        self.assertFalse(evaluation.lock_requested)
        self.assertEqual(evaluation.state, ControllerState.ACTIVE)
        self.assertEqual(self.locker.calls, 0)

    def test_locks_at_exact_timeout(self) -> None:
        self.clock.advance(10)

        evaluation = self.controller.evaluate_once()

        self.assertTrue(evaluation.lock_requested)
        self.assertEqual(evaluation.state, ControllerState.LOCKED)
        self.assertEqual(self.locker.calls, 1)

    def test_requests_only_one_lock_per_idle_episode(self) -> None:
        self.clock.advance(10)
        self.controller.evaluate_once()
        self.clock.advance(30)

        second = self.controller.evaluate_once()

        self.assertFalse(second.lock_requested)
        self.assertEqual(self.locker.calls, 1)

    def test_new_activity_rearms_future_lock(self) -> None:
        self.clock.advance(10)
        self.controller.evaluate_once()
        self.clock.advance(1)
        self.manager.record(ActivityKind.MOUSE_CLICK)
        active = self.controller.evaluate_once()
        self.clock.advance(10)

        locked_again = self.controller.evaluate_once()

        self.assertEqual(active.state, ControllerState.ACTIVE)
        self.assertTrue(locked_again.lock_requested)
        self.assertEqual(self.locker.calls, 2)

    def test_presence_signal_can_hold_workstation_unlocked(self) -> None:
        controller = IdleLockController(
            self.manager,
            self.locker,
            idle_timeout_seconds=10,
            poll_interval_seconds=1,
            clock=self.clock,
            signal_reader=lambda: PresenceSignals(user_present=True),
        )
        self.clock.advance(10)

        evaluation = controller.evaluate_once()

        self.assertFalse(evaluation.lock_requested)
        self.assertEqual(evaluation.state, ControllerState.ACTIVE)
        self.assertEqual(self.locker.calls, 0)

    def test_failed_lock_is_not_marked_successful_and_can_retry(self) -> None:
        self.locker.error = RuntimeError("native failure")
        self.clock.advance(10)
        with self.assertLogs("sentinel_lock.idle", logging.ERROR):
            failed = self.controller.evaluate_once()
        self.locker.error = None

        retried = self.controller.evaluate_once()

        self.assertFalse(failed.lock_requested)
        self.assertEqual(failed.state, ControllerState.ACTIVE)
        self.assertTrue(retried.lock_requested)
        self.assertEqual(self.locker.calls, 2)


if __name__ == "__main__":
    unittest.main()
