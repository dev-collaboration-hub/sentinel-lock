from threading import Event
import time
import tracemalloc
import unittest

from sentinel_lock.activity import ActivityKind, ActivityManager
from sentinel_lock.idle import IdleLockController
from sentinel_lock.monitors import KeyboardMonitor, MouseMonitor
from sentinel_lock.reliability import MonitorSupervisor
from tests.helpers import FakeClock, FakeListener, RecordingLocker


CPU_BUDGET_SECONDS = 10.0
PEAK_MEMORY_BUDGET_BYTES = 32 * 1024 * 1024
STRESS_EVENT_COUNT = 10_000


class MonitorRecoveryTests(unittest.TestCase):
    def test_supervisor_restarts_failed_keyboard_listener(self) -> None:
        manager = ActivityManager()
        listeners: list[FakeListener] = []

        def factory(**callbacks: object) -> FakeListener:
            listener = FakeListener(**callbacks)
            listeners.append(listener)
            return listener

        monitor = KeyboardMonitor(manager, listener_factory=factory)
        monitor.start()
        listeners[0].fail()

        report = MonitorSupervisor([monitor]).poll()

        self.assertEqual(report.checked, 1)
        self.assertEqual(report.restarted, 1)
        self.assertEqual(report.failures, 0)
        self.assertEqual(len(listeners), 2)
        self.assertTrue(listeners[1].is_alive())

    def test_mouse_restart_resets_pending_movement_confirmation(self) -> None:
        clock = FakeClock()
        manager = ActivityManager(clock=clock)
        listeners: list[FakeListener] = []

        def factory(**callbacks: object) -> FakeListener:
            listener = FakeListener(**callbacks)
            listeners.append(listener)
            return listener

        monitor = MouseMonitor(
            manager,
            listener_factory=factory,
            clock=clock,
        )
        monitor.start()
        listeners[0].callbacks["on_move"](1, 1)
        listeners[0].fail()
        MonitorSupervisor([monitor]).poll()

        clock.advance(0.10)
        listeners[1].callbacks["on_move"](2, 2)
        self.assertEqual(manager.snapshot().sequence, 0)

        clock.advance(0.10)
        listeners[1].callbacks["on_move"](3, 3)
        self.assertEqual(manager.snapshot().sequence, 1)

    def test_supervisor_retries_after_transient_restart_failure(self) -> None:
        manager = ActivityManager()
        calls = 0
        listeners: list[FakeListener] = []

        def factory(**callbacks: object) -> FakeListener:
            nonlocal calls
            calls += 1
            if calls == 2:
                raise RuntimeError("transient hook failure")
            listener = FakeListener(**callbacks)
            listeners.append(listener)
            return listener

        monitor = KeyboardMonitor(manager, listener_factory=factory)
        monitor.start()
        listeners[0].fail()
        supervisor = MonitorSupervisor([monitor])

        with self.assertLogs("sentinel_lock.reliability", level="ERROR"):
            failed = supervisor.poll()
        recovered = supervisor.poll()

        self.assertEqual(failed.failures, 1)
        self.assertEqual(recovered.restarted, 1)
        self.assertTrue(monitor.is_alive())

    def test_controller_maintenance_failure_is_isolated(self) -> None:
        clock = FakeClock()
        manager = ActivityManager(clock=clock)
        locker = RecordingLocker()
        stop_event = Event()
        calls = 0

        def broken_maintenance() -> None:
            nonlocal calls
            calls += 1
            stop_event.set()
            raise RuntimeError("maintenance failure")

        controller = IdleLockController(
            manager,
            locker,
            idle_timeout_seconds=10,
            poll_interval_seconds=1,
            clock=clock,
            maintenance_callback=broken_maintenance,
        )

        with self.assertLogs("sentinel_lock.idle", level="ERROR"):
            controller.run(stop_event)

        self.assertEqual(calls, 1)
        self.assertEqual(locker.calls, 0)


class PerformanceGuardTests(unittest.TestCase):
    def test_high_frequency_keyboard_callbacks_stay_bounded(self) -> None:
        manager = ActivityManager()
        listener = FakeListener()

        def factory(**callbacks: object) -> FakeListener:
            listener.callbacks = callbacks
            return listener

        monitor = KeyboardMonitor(manager, listener_factory=factory)
        monitor.start()

        tracemalloc.start()
        started = time.process_time()
        for _ in range(STRESS_EVENT_COUNT):
            listener.callbacks["on_press"]("discarded-key")
        cpu_seconds = time.process_time() - started
        _current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        self.assertEqual(manager.snapshot().sequence, STRESS_EVENT_COUNT)
        self.assertLess(cpu_seconds, CPU_BUDGET_SECONDS)
        self.assertLess(peak, PEAK_MEMORY_BUDGET_BYTES)

    def test_high_frequency_mouse_filter_stays_bounded(self) -> None:
        clock = FakeClock()
        manager = ActivityManager(clock=clock)
        listener = FakeListener()

        def factory(**callbacks: object) -> FakeListener:
            listener.callbacks = callbacks
            return listener

        monitor = MouseMonitor(
            manager,
            listener_factory=factory,
            clock=clock,
        )
        monitor.start()

        tracemalloc.start()
        started = time.process_time()
        for point in range(STRESS_EVENT_COUNT):
            clock.advance(0.01)
            listener.callbacks["on_move"](point, point)
        cpu_seconds = time.process_time() - started
        _current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        sequence = manager.snapshot().sequence
        self.assertGreater(sequence, 100)
        self.assertLess(sequence, 1_000)
        self.assertLess(cpu_seconds, CPU_BUDGET_SECONDS)
        self.assertLess(peak, PEAK_MEMORY_BUDGET_BYTES)


class LongRunStabilityTests(unittest.TestCase):
    def test_one_thousand_idle_episodes_never_duplicate_lock(self) -> None:
        clock = FakeClock()
        manager = ActivityManager(clock=clock)
        locker = RecordingLocker()
        controller = IdleLockController(
            manager,
            locker,
            idle_timeout_seconds=10,
            poll_interval_seconds=1,
            clock=clock,
        )

        for _ in range(1_000):
            clock.advance(10)
            first = controller.evaluate_once()
            self.assertTrue(first.lock_requested)

            for _duplicate_probe in range(3):
                clock.advance(1)
                duplicate = controller.evaluate_once()
                self.assertFalse(duplicate.lock_requested)

            manager.record(ActivityKind.KEYBOARD)
            active = controller.evaluate_once()
            self.assertFalse(active.lock_requested)

        self.assertEqual(locker.calls, 1_000)

    def test_repeated_forced_lock_requests_do_not_bypass_episode_guard(self) -> None:
        clock = FakeClock()
        manager = ActivityManager(clock=clock)
        locker = RecordingLocker()
        controller = IdleLockController(
            manager,
            locker,
            idle_timeout_seconds=10,
            poll_interval_seconds=1,
            clock=clock,
        )

        controller.request_lock()
        first = controller.evaluate_once()
        controller.request_lock()
        controller.request_lock()
        duplicate = controller.evaluate_once()

        self.assertTrue(first.lock_requested)
        self.assertFalse(duplicate.lock_requested)
        self.assertEqual(locker.calls, 1)


if __name__ == "__main__":
    unittest.main()
