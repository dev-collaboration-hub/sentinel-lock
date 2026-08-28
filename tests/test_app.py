from threading import Event
import unittest

from sentinel_lock.app import SentinelLockApplication
from sentinel_lock.config import load_config
from tests.helpers import RecordingLocker


class FakeMonitor:
    def __init__(self, *, start_error: Exception | None = None) -> None:
        self.start_error = start_error
        self.started = False
        self.stopped = False
        self.joined_with: float | None = None

    def start(self) -> None:
        if self.start_error is not None:
            raise self.start_error
        self.started = True

    def stop(self) -> None:
        self.stopped = True

    def join(self, timeout: float | None = None) -> None:
        self.joined_with = timeout


class FakeRuntimeExperience:
    def __init__(self) -> None:
        self.started = False
        self.stopped = False
        self.controller = None
        self.stop_event = None
        self.evaluations = []
        self.resumes = 0

    def start(self, controller: object, stop_event: Event) -> bool:
        self.started = True
        self.controller = controller
        self.stop_event = stop_event
        return True

    def observe(self, evaluation: object) -> None:
        self.evaluations.append(evaluation)

    def note_resume(self) -> None:
        self.resumes += 1

    def stop(self) -> None:
        self.stopped = True


class ApplicationTests(unittest.TestCase):
    def test_cleanly_stops_every_started_monitor(self) -> None:
        first = FakeMonitor()
        second = FakeMonitor()
        stop_event = Event()
        stop_event.set()
        application = SentinelLockApplication(
            load_config(),
            monitors=[first, second],
            locker=RecordingLocker(),
        )
        application.run(stop_event)
        self.assertTrue(first.started)
        self.assertTrue(second.started)
        self.assertTrue(first.stopped)
        self.assertTrue(second.stopped)
        self.assertEqual(first.joined_with, 2.0)
        self.assertEqual(second.joined_with, 2.0)

    def test_runtime_experience_starts_and_stops_with_application(self) -> None:
        monitor = FakeMonitor()
        runtime = FakeRuntimeExperience()
        stop_event = Event()
        stop_event.set()
        application = SentinelLockApplication(
            load_config(),
            monitors=[monitor],
            locker=RecordingLocker(),
            runtime_experience=runtime,
        )
        application.run(stop_event)
        self.assertTrue(runtime.started)
        self.assertTrue(runtime.stopped)
        self.assertIsNotNone(runtime.controller)
        self.assertIs(runtime.stop_event, stop_event)

    def test_startup_failure_stops_only_prior_started_monitors(self) -> None:
        first = FakeMonitor()
        second = FakeMonitor(start_error=RuntimeError("cannot start"))
        application = SentinelLockApplication(
            load_config(),
            monitors=[first, second],
            locker=RecordingLocker(),
        )
        with self.assertRaisesRegex(RuntimeError, "cannot start"):
            application.run(Event())
        self.assertTrue(first.stopped)
        self.assertEqual(first.joined_with, 2.0)
        self.assertFalse(second.stopped)


if __name__ == "__main__":
    unittest.main()
