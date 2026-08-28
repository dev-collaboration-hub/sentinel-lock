# Contributing to Sentinel Lock

Thank you for helping improve Sentinel Lock.

## Non-negotiable dependency boundary

Sentinel Lock runtime/application code must remain Python standard-library +
Windows system APIs only.

Do not add:

- pip runtime dependencies;
- `requirements.txt`, `pyproject.toml`, `setup.py`, or `setup.cfg`;
- third-party keyboard/mouse hook packages;
- third-party tray/UI packages;
- third-party frozen-app packagers.

`python tests/check_stdlib_only.py` must stay green.

## Pull request requirements

- explain the security or user impact;
- include tests for new behavior;
- pass the stdlib dependency gate, unit tests, and compilation checks;
- update relevant documentation;
- preserve keyboard/mouse-only scope and privacy boundaries.

Input contents, pointer coordinates, mouse-button identity, and user activity
histories must never be logged or committed as fixtures.

By contributing, you agree that your contribution is licensed under the MIT
License.
