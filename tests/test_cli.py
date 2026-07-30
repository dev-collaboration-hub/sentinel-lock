from contextlib import redirect_stdout
from io import StringIO
import unittest

from sentinel_lock.cli import main


class CommandLineTests(unittest.TestCase):
    def test_check_config_reports_effective_values(self) -> None:
        output = StringIO()

        with redirect_stdout(output):
            result = main(
                [
                    "--check-config",
                    "--dry-run",
                    "--timeout",
                    "30",
                    "--poll-interval",
                    "0.5",
                ]
            )

        self.assertEqual(result, 0)
        self.assertIn("Configuration is valid", output.getvalue())
        self.assertIn("Idle timeout: 30 seconds", output.getvalue())
        self.assertIn("Mode: dry run", output.getvalue())


if __name__ == "__main__":
    unittest.main()
