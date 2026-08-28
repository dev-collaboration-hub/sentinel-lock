import logging
from threading import Event
import unittest

from sentinel_lock.activity import ActivityKind, ActivityManager
from sentinel_lock.idle import ControllerState, IdleLockController, should_lock
from tests.helpers import FakeClock, RecordingLocker


class LockPolicyTests(unittest.TestCase):
    def test_does_not_lock_before_timeout(self) -> None:
        self.assertFalse(should_lock(9.9, 10))

    def test_idle_timeout_requests_lock(self) -> None:
        self.assertTrue(should_lock(10, 10))


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

    def test_keyboard_activity_rearms_future_lock(self) -> None:
        self.clock.advance(10)
        self.controller.evaluate_once()
        self.clock.advance(1)
        self.manager.record(ActivityKind.KEYBOARD)
        active = self.controller.evaluate_once()
        self.clock.advance(10)
        locked_again = self.controller.evaluate_once()
        self.assertEqual(active.state, ControllerState.ACTIVE)
        self.assertTrue(locked_again.lock_requested)
        self.assertEqual(self.locker.calls, 2)

    def test_mouse_activity_rearms_future_lock(self) -> None:
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

    def test_runtime_lock_request_locks_before_idle_timeout(self) -> None:
        self.clock.advance(1)
        self.controller.request_lock()
        evaluation = self.controller.evaluate_once()
        self.assertTrue(evaluation.lock_requested)
        self.assertEqual(evaluation.state, ControllerState.LOCKED)
        self.assertEqual(self.locker.calls, 1)

    def test_resume_rebaselines_idle_without_faking_input_activity(self) -> None:
        self.clock.advance(100)
        original_sequence = self.manager.snapshot().sequence
        self.controller.handle_resume()
        resumed = self.controller.evaluate_once()
        self.clock.advance(9)
        before_timeout = self.controller.evaluate_once()
        self.clock.advance(1)
        at_timeout = self.controller.evaluate_once()
        self.assertEqual(resumed.idle_seconds, 0)
        self.assertFalse(before_timeout.lock_requested)
        self.assertTrue(at_timeout.lock_requested)
        self.assertEqual(self.manager.snapshot().sequence, original_sequence)

    def test_new_activity_clears_resume_baseline(self) -> None:
        self.clock.advance(100)
        self.controller.handle_resume()
        self.clock.advance(2)
        self.manager.record(ActivityKind.KEYBOARD)
        self.clock.advance(3)
        evaluation = self.controller.evaluate_once()
        self.assertEqual(evaluation.idle_seconds, 3)

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


class FakeResumeDetector:
    def __init__(self) -> None:
        self.calls = 0

    def poll(self) -> bool:
        self.calls += 1
        return self.calls == 1


class ObserverTests(unittest.TestCase):
    def test_run_reports_resume_and_evaluation(self) -> None:
        clock = FakeClock()
        manager = ActivityManager(clock=clock)
        locker = RecordingLocker()
        stop_event = Event()
        evaluations = []
        resumes = []

        def observe(evaluation: object) -> None:
            evaluations.append(evaluation)
            stop_event.set()

        controller = IdleLockController(
            manager,
            locker,
            idle_timeout_seconds=10,
            poll_interval_seconds=1,
            clock=clock,
            resume_detector=FakeResumeDetector(),
            evaluation_observer=observe,
            resume_observer=lambda: resumes.append(True),
        )
        controller.run(stop_event)
        self.assertEqual(len(evaluations), 1)
        self.assertEqual(resumes, [True])
        self.assertEqual(locker.calls, 0)


if __name__ == "__main__":
    unittest.main()
