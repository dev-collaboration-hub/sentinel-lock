"""Stdlib-only Windows keyboard and mouse hook listeners.

The listeners call Win32 directly through ``ctypes``. They intentionally do not
copy keyboard hook structures or pointer coordinates into application state.
"""

from __future__ import annotations

import ctypes
from ctypes import wintypes
import logging
import os
from threading import Event, Lock, Thread
from typing import Any, Callable

WH_KEYBOARD_LL = 13
WH_MOUSE_LL = 14
HC_ACTION = 0
WM_QUIT = 0x0012
WM_KEYDOWN = 0x0100
WM_SYSKEYDOWN = 0x0104
WM_MOUSEMOVE = 0x0200
WM_LBUTTONDOWN = 0x0201
WM_RBUTTONDOWN = 0x0204
WM_MBUTTONDOWN = 0x0207
WM_XBUTTONDOWN = 0x020B
_MOUSE_BUTTON_DOWN_MESSAGES = {
    WM_LBUTTONDOWN,
    WM_RBUTTONDOWN,
    WM_MBUTTONDOWN,
    WM_XBUTTONDOWN,
}

LRESULT = ctypes.c_ssize_t
HOOKPROC = ctypes.WINFUNCTYPE(LRESULT, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM)


class Win32HookError(OSError):
    """Raised when a native input hook cannot be installed or managed."""


class _Win32HookListener:
    """Own one low-level Windows hook and its required message-loop thread."""

    hook_id: int

    def __init__(self, *, logger: logging.Logger | None = None) -> None:
        self._logger = logger or logging.getLogger(__name__)
        self._thread: Thread | None = None
        self._thread_id: int | None = None
        self._hook: Any | None = None
        self._hook_proc: Any | None = None
        self._ready = Event()
        self._stopping = Event()
        self._start_error: BaseException | None = None
        self._lock = Lock()

    def start(self) -> None:
        if os.name != "nt":
            raise Win32HookError("native input hooks are supported only on Windows")
        with self._lock:
            if self._thread is not None and self._thread.is_alive():
                return
            self._ready.clear()
            self._stopping.clear()
            self._start_error = None
            self._thread = Thread(target=self._run, name=self._thread_name(), daemon=True)
            self._thread.start()
        if not self._ready.wait(5.0):
            raise Win32HookError("Windows input hook startup timed out")
        if self._start_error is not None:
            raise Win32HookError(str(self._start_error)) from self._start_error

    def stop(self) -> None:
        self._stopping.set()
        thread_id = self._thread_id
        if thread_id is None or os.name != "nt":
            return
        user32 = ctypes.WinDLL("user32", use_last_error=True)
        user32.PostThreadMessageW.argtypes = [wintypes.DWORD, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
        user32.PostThreadMessageW.restype = wintypes.BOOL
        if not user32.PostThreadMessageW(thread_id, WM_QUIT, 0, 0):
            error = ctypes.get_last_error()
            if error:
                self._logger.debug("PostThreadMessageW failed during hook shutdown: %s", error)

    def join(self, timeout: float | None = None) -> None:
        thread = self._thread
        if thread is not None:
            thread.join(timeout)

    def is_alive(self) -> bool:
        thread = self._thread
        return bool(thread is not None and thread.is_alive() and self._hook is not None)

    def _run(self) -> None:
        try:
            user32 = ctypes.WinDLL("user32", use_last_error=True)
            kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

            kernel32.GetCurrentThreadId.argtypes = []
            kernel32.GetCurrentThreadId.restype = wintypes.DWORD
            kernel32.GetModuleHandleW.argtypes = [wintypes.LPCWSTR]
            kernel32.GetModuleHandleW.restype = wintypes.HMODULE

            user32.SetWindowsHookExW.argtypes = [ctypes.c_int, HOOKPROC, wintypes.HINSTANCE, wintypes.DWORD]
            user32.SetWindowsHookExW.restype = wintypes.HANDLE
            user32.UnhookWindowsHookEx.argtypes = [wintypes.HANDLE]
            user32.UnhookWindowsHookEx.restype = wintypes.BOOL
            user32.CallNextHookEx.argtypes = [wintypes.HANDLE, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM]
            user32.CallNextHookEx.restype = LRESULT
            user32.GetMessageW.argtypes = [ctypes.POINTER(wintypes.MSG), wintypes.HWND, wintypes.UINT, wintypes.UINT]
            user32.GetMessageW.restype = wintypes.BOOL
            user32.TranslateMessage.argtypes = [ctypes.POINTER(wintypes.MSG)]
            user32.DispatchMessageW.argtypes = [ctypes.POINTER(wintypes.MSG)]

            self._thread_id = int(kernel32.GetCurrentThreadId())

            @HOOKPROC
            def hook_proc(n_code: int, w_param: int, l_param: int) -> int:
                if n_code >= HC_ACTION:
                    try:
                        self._handle_message(int(w_param))
                    except Exception:
                        self._logger.exception("Windows input hook callback failed")
                return int(user32.CallNextHookEx(None, n_code, w_param, l_param))

            self._hook_proc = hook_proc
            module = kernel32.GetModuleHandleW(None)
            hook = user32.SetWindowsHookExW(self.hook_id, hook_proc, module, 0)
            if not hook:
                raise ctypes.WinError(ctypes.get_last_error())
            self._hook = hook
            self._ready.set()

            message = wintypes.MSG()
            while not self._stopping.is_set():
                result = user32.GetMessageW(ctypes.byref(message), None, 0, 0)
                if result == 0:
                    break
                if result == -1:
                    raise ctypes.WinError(ctypes.get_last_error())
                user32.TranslateMessage(ctypes.byref(message))
                user32.DispatchMessageW(ctypes.byref(message))
        except BaseException as exc:
            if not self._ready.is_set():
                self._start_error = exc
            else:
                self._logger.exception("Windows input hook thread stopped unexpectedly")
        finally:
            hook = self._hook
            self._hook = None
            if hook is not None and os.name == "nt":
                try:
                    user32 = ctypes.WinDLL("user32", use_last_error=True)
                    user32.UnhookWindowsHookEx(hook)
                except Exception:
                    self._logger.debug("UnhookWindowsHookEx failed during cleanup", exc_info=True)
            self._thread_id = None
            self._ready.set()

    def _thread_name(self) -> str:
        return f"sentinel-lock-hook-{self.hook_id}"

    def _handle_message(self, w_param: int) -> None:
        raise NotImplementedError


class Win32KeyboardListener(_Win32HookListener):
    """Low-level keyboard listener that emits only key-press occurrence."""

    hook_id = WH_KEYBOARD_LL

    def __init__(self, *, on_press: Callable[[object], None], logger: logging.Logger | None = None) -> None:
        super().__init__(logger=logger)
        self._on_press = on_press

    def _handle_message(self, w_param: int) -> None:
        if w_param in (WM_KEYDOWN, WM_SYSKEYDOWN):
            # Deliberately do not dereference lParam/KBDLLHOOKSTRUCT.
            self._on_press(None)


class Win32MouseListener(_Win32HookListener):
    """Low-level mouse listener that emits movement/click occurrence only."""

    hook_id = WH_MOUSE_LL

    def __init__(
        self,
        *,
        on_move: Callable[[int, int], None],
        on_click: Callable[[int, int, object, bool], None],
        logger: logging.Logger | None = None,
    ) -> None:
        super().__init__(logger=logger)
        self._on_move = on_move
        self._on_click = on_click

    def _handle_message(self, w_param: int) -> None:
        if w_param == WM_MOUSEMOVE:
            # Coordinates are intentionally never read from MSLLHOOKSTRUCT.
            self._on_move(0, 0)
        elif w_param in _MOUSE_BUTTON_DOWN_MESSAGES:
            # Button identity and coordinates are intentionally discarded.
            self._on_click(0, 0, None, True)
