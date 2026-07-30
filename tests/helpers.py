"""Deterministic test doubles."""

from __future__ import annotations

from typing import Any


class FakeClock:
    def __init__(self, value: float = 0.0) -> None:
        self.value = value

    def __call__(self) -> float:
        return self.value

    def advance(self, seconds: float) -> None:
        self.value += seconds


class RecordingLocker:
    def __init__(self, *, error: Exception | None = None) -> None:
        self.calls = 0
        self.error = error

    def lock(self) -> None:
        self.calls += 1
        if self.error is not None:
            raise self.error


class FakeListener:
    def __init__(self, **callbacks: Any) -> None:
        self.callbacks = callbacks
        self.started = False
        self.stopped = False
        self.join_timeout: float | None = None

    def start(self) -> None:
        self.started = True

    def stop(self) -> None:
        self.stopped = True

    def join(self, timeout: float | None = None) -> None:
        self.join_timeout = timeout
