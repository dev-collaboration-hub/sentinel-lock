"""Run Sentinel Lock from a source checkout without installing a package."""

from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from sentinel_lock.cli import main

raise SystemExit(main())
