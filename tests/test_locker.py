import unittest

from sentinel_lock.locker import (
    DryRunWorkstationLocker,
    UnsupportedPlatformError,
    WindowsWorkstationLocker,
    WorkstationLockError,
)


class LockerTests(unittest.TestCase):
    def test_native_locker_rejects_non_windows_platform(self) -> None:
        with self.assertRaises(UnsupportedPlatformError):
            WindowsWorkstationLocker(platform_name="linux")

    def test_native_locker_accepts_successful_api_result(self) -> None:
        locker = WindowsWorkstationLocker(
            platform_name="win32",
            lock_api=lambda: 1,
        )

        locker.lock()

    def test_native_locker_raises_on_failed_api_result(self) -> None:
        locker = WindowsWorkstationLocker(
            platform_name="win32",
            lock_api=lambda: 0,
        )

        with self.assertRaises(WorkstationLockError):
            locker.lock()

    def test_dry_run_never_calls_native_api(self) -> None:
        locker = DryRunWorkstationLocker()

        with self.assertLogs("sentinel_lock.locker", level="WARNING"):
            locker.lock()


if __name__ == "__main__":
    unittest.main()
