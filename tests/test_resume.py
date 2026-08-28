import unittest

from sentinel_lock.resume import ResumeDetector
from tests.helpers import FakeClock


class ResumeDetectorTests(unittest.TestCase):
    def test_normal_polling_is_not_resume(self) -> None:
        monotonic = FakeClock()
        wall = FakeClock()
        detector = ResumeDetector(
            gap_seconds=10,
            monotonic_clock=monotonic,
            wall_clock=wall,
        )
        monotonic.advance(1)
        wall.advance(1)
        self.assertFalse(detector.poll())

    def test_long_gap_is_resume(self) -> None:
        monotonic = FakeClock()
        wall = FakeClock()
        detector = ResumeDetector(
            gap_seconds=10,
            monotonic_clock=monotonic,
            wall_clock=wall,
        )
        monotonic.advance(1)
        wall.advance(15)
        self.assertTrue(detector.poll())
        self.assertFalse(detector.poll())

    def test_gap_must_be_positive(self) -> None:
        with self.assertRaisesRegex(ValueError, "positive"):
            ResumeDetector(gap_seconds=0)


if __name__ == "__main__":
    unittest.main()
