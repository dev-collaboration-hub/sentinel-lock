import unittest

from sentinel_lock.idle import ControllerState, IdleEvaluation
from sentinel_lock.runtime_ui import RuntimeStatus


class RuntimeStatusTests(unittest.TestCase):
    def test_status_tracks_only_idle_state(self) -> None:
        status = RuntimeStatus()
        snapshot = status.observe(
            IdleEvaluation(
                idle_seconds=12.5,
                activity_sequence=42,
                state=ControllerState.ACTIVE,
                lock_requested=False,
            )
        )
        self.assertEqual(snapshot.idle_seconds, 12.5)
        self.assertEqual(snapshot.state, ControllerState.ACTIVE)
        self.assertFalse(hasattr(snapshot, "activity_sequence"))
        self.assertFalse(hasattr(snapshot, "key"))
        self.assertFalse(hasattr(snapshot, "coordinates"))

    def test_resume_resets_visible_idle_status(self) -> None:
        status = RuntimeStatus()
        status.observe(
            IdleEvaluation(25, 1, ControllerState.LOCKED, True)
        )
        resumed = status.note_resume()
        self.assertEqual(resumed.state, ControllerState.ACTIVE)
        self.assertEqual(resumed.idle_seconds, 0)
        self.assertEqual(resumed.resumed_count, 1)


if __name__ == "__main__":
    unittest.main()
