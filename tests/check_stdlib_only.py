"""Fail CI if Sentinel Lock gains a non-stdlib Python dependency."""

from __future__ import annotations

import ast
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
LOCAL_ROOTS = {"sentinel_lock"}
PLATFORM_STDLIB = {"winreg"}
FORBIDDEN_TEXT = {"pynput", "pystray", "PIL", "PyInstaller", "pyinstaller"}


def imported_roots(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            roots.add(node.module.split(".", 1)[0])
    return roots


def main() -> int:
    allowed = set(sys.stdlib_module_names) | LOCAL_ROOTS | PLATFORM_STDLIB
    failures: list[str] = []

    for path in sorted(SRC.rglob("*.py")):
        text = path.read_text(encoding="utf-8")
        for token in FORBIDDEN_TEXT:
            if token in text:
                failures.append(f"{path.relative_to(ROOT)} contains forbidden dependency token {token!r}")
        for root in sorted(imported_roots(path) - allowed):
            failures.append(f"{path.relative_to(ROOT)} imports non-stdlib module {root!r}")

    for manifest in (ROOT / "requirements.txt",):
        if manifest.exists() and manifest.read_text(encoding="utf-8").strip():
            failures.append(f"{manifest.name} must be absent or empty")

    workflows = ROOT / ".github" / "workflows"
    if workflows.exists():
        for path in workflows.glob("*.yml"):
            text = path.read_text(encoding="utf-8").lower()
            if "pip install" in text:
                failures.append(f"{path.relative_to(ROOT)} contains pip install")
            if "pyinstaller" in text:
                failures.append(f"{path.relative_to(ROOT)} contains PyInstaller")

    if failures:
        print("Stdlib-only dependency gate FAILED:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Stdlib-only dependency gate passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
