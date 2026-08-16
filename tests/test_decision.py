import unittest

from sentinel_lock.decision import PresenceSignals, SmartLockDecisionEngine


class SmartLockDecisionEngineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = SmartLockDecisionEngine(idle_timeout_seconds=10)

    def test_does_not_lock_before_timeout(self) -> None:
        self.assertFalse(self.engine.should_lock(9.9))

    def test_idle_only_behavior_is_preserved(self) -> None:
        self.assertTrue(self.engine.should_lock(10))

    def test_detected_user_blocks_lock(self) -> None:
        signals = PresenceSignals(user_present=True)
        self.assertFalse(self.engine.should_lock(10, signals))

    def test_nearby_trusted_device_blocks_lock(self) -> None:
        signals = PresenceSignals(trusted_device_nearby=True)
        self.assertFalse(self.engine.should_lock(10, signals))


if __name__ == "__main__":
    unittest.main()
