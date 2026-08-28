"""Stdlib-only Windows notification-area backend using Shell_NotifyIconW."""

from __future__ import annotations

import ctypes
from ctypes import wintypes
import logging
import os
from threading import Event, Lock, Thread
from typing import Callable

WM_APP = 0x8000
WM_TRAY = WM_APP + 1
WM_COMMAND = 0x0111
WM_DESTROY = 0x0002
WM_CLOSE = 0x0010
WM_RBUTTONUP = 0x0205
WM_CONTEXTMENU = 0x007B

NIM_ADD = 0x00000000
NIM_MODIFY = 0x00000001
NIM_DELETE = 0x00000002
NIF_MESSAGE = 0x00000001
NIF_ICON = 0x00000002
NIF_TIP = 0x00000004
NIF_INFO = 0x00000010
NIIF_INFO = 0x00000001

MF_STRING = 0x00000000
MF_GRAYED = 0x00000001
MF_SEPARATOR = 0x00000800
TPM_RETURNCMD = 0x0100
TPM_NONOTIFY = 0x0080

IDI_APPLICATION = 32512
CMD_STATUS = 1000
CMD_LOCK_NOW = 1001
CMD_EXIT = 1002

LRESULT = ctypes.c_ssize_t
WNDPROC = ctypes.WINFUNCTYPE(LRESULT, wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM)


class GUID(ctypes.Structure):
    _fields_ = [
        ("Data1", wintypes.DWORD),
        ("Data2", wintypes.WORD),
        ("Data3", wintypes.WORD),
        ("Data4", ctypes.c_ubyte * 8),
    ]


class NOTIFYICONDATAW(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("hWnd", wintypes.HWND),
        ("uID", wintypes.UINT),
        ("uFlags", wintypes.UINT),
        ("uCallbackMessage", wintypes.UINT),
        ("hIcon", wintypes.HICON),
        ("szTip", wintypes.WCHAR * 128),
        ("dwState", wintypes.DWORD),
        ("dwStateMask", wintypes.DWORD),
        ("szInfo", wintypes.WCHAR * 256),
        ("uTimeoutOrVersion", wintypes.UINT),
        ("szInfoTitle", wintypes.WCHAR * 64),
        ("dwInfoFlags", wintypes.DWORD),
        ("guidItem", GUID),
        ("hBalloonIcon", wintypes.HICON),
    ]


class WNDCLASSW(ctypes.Structure):
    _fields_ = [
        ("style", wintypes.UINT),
        ("lpfnWndProc", WNDPROC),
        ("cbClsExtra", ctypes.c_int),
        ("cbWndExtra", ctypes.c_int),
        ("hInstance", wintypes.HINSTANCE),
        ("hIcon", wintypes.HICON),
        ("hCursor", wintypes.HANDLE),
        ("hbrBackground", wintypes.HBRUSH),
        ("lpszMenuName", wintypes.LPCWSTR),
        ("lpszClassName", wintypes.LPCWSTR),
    ]


class POINT(ctypes.Structure):
    _fields_ = [("x", wintypes.LONG), ("y", wintypes.LONG)]


class Win32TrayError(OSError):
    """Raised when the native notification-area backend cannot start."""


class Win32TrayBackend:
    """Own a hidden Win32 window and one Shell_NotifyIcon notification icon."""

    def __init__(
        self,
        *,
        status_provider: Callable[[], str],
        lock_now: Callable[[], None],
        exit_app: Callable[[], None],
        logger: logging.Logger | None = None,
    ) -> None:
        self._status_provider = status_provider
        self._lock_now = lock_now
        self._exit_app = exit_app
        self._logger = logger or logging.getLogger(__name__)
        self._thread: Thread | None = None
        self._thread_id: int | None = None
        self._hwnd: int | None = None
        self._ready = Event()
        self._start_error: BaseException | None = None
        self._wndproc: object | None = None
        self._lock = Lock()

    def start(self) -> None:
        if os.name != "nt":
            raise Win32TrayError("system tray is supported only on Windows")
        with self._lock:
            if self._thread is not None and self._thread.is_alive():
                return
            self._ready.clear()
            self._start_error = None
            self._thread = Thread(target=self._run, name="sentinel-lock-tray", daemon=True)
            self._thread.start()
        if not self._ready.wait(5.0):
            raise Win32TrayError("system tray startup timed out")
        if self._start_error is not None:
            raise Win32TrayError(str(self._start_error)) from self._start_error

    def stop(self) -> None:
        hwnd = self._hwnd
        if hwnd is None or os.name != "nt":
            return
        user32 = ctypes.WinDLL("user32", use_last_error=True)
        user32.PostMessageW(hwnd, WM_CLOSE, 0, 0)

    def join(self, timeout: float | None = None) -> None:
        thread = self._thread
        if thread is not None:
            thread.join(timeout)

    def update_tip(self, text: str) -> None:
        hwnd = self._hwnd
        if hwnd is None or os.name != "nt":
            return
        shell32 = ctypes.WinDLL("shell32", use_last_error=True)
        nid = self._nid(hwnd, flags=NIF_TIP)
        nid.szTip = text[:127]
        shell32.Shell_NotifyIconW(NIM_MODIFY, ctypes.byref(nid))

    def notify(self, title: str, message: str) -> None:
        hwnd = self._hwnd
        if hwnd is None or os.name != "nt":
            return
        shell32 = ctypes.WinDLL("shell32", use_last_error=True)
        nid = self._nid(hwnd, flags=NIF_INFO)
        nid.szInfoTitle = title[:63]
        nid.szInfo = message[:255]
        nid.dwInfoFlags = NIIF_INFO
        shell32.Shell_NotifyIconW(NIM_MODIFY, ctypes.byref(nid))

    def _run(self) -> None:
        try:
            user32 = ctypes.WinDLL("user32", use_last_error=True)
            kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
            shell32 = ctypes.WinDLL("shell32", use_last_error=True)

            kernel32.GetModuleHandleW.argtypes = [wintypes.LPCWSTR]
            kernel32.GetModuleHandleW.restype = wintypes.HMODULE
            kernel32.GetCurrentThreadId.argtypes = []
            kernel32.GetCurrentThreadId.restype = wintypes.DWORD

            @WNDPROC
            def wndproc(hwnd: int, msg: int, w_param: int, l_param: int) -> int:
                if msg == WM_TRAY and int(l_param) in (WM_RBUTTONUP, WM_CONTEXTMENU):
                    self._show_menu(hwnd)
                    return 0
                if msg == WM_COMMAND:
                    command = int(w_param) & 0xFFFF
                    if command == CMD_LOCK_NOW:
                        self._lock_now()
                        return 0
                    if command == CMD_EXIT:
                        self._exit_app()
                        user32.DestroyWindow(hwnd)
                        return 0
                if msg == WM_DESTROY:
                    user32.PostQuitMessage(0)
                    return 0
                return int(user32.DefWindowProcW(hwnd, msg, w_param, l_param))

            self._wndproc = wndproc
            instance = kernel32.GetModuleHandleW(None)
            class_name = f"SentinelLockTray_{os.getpid()}_{id(self)}"
            wc = WNDCLASSW()
            wc.lpfnWndProc = wndproc
            wc.hInstance = instance
            wc.lpszClassName = class_name
            atom = user32.RegisterClassW(ctypes.byref(wc))
            if not atom:
                raise ctypes.WinError(ctypes.get_last_error())

            hwnd = user32.CreateWindowExW(
                0,
                class_name,
                "Sentinel Lock",
                0,
                0,
                0,
                0,
                0,
                None,
                None,
                instance,
                None,
            )
            if not hwnd:
                raise ctypes.WinError(ctypes.get_last_error())
            self._hwnd = int(hwnd)
            self._thread_id = int(kernel32.GetCurrentThreadId())

            user32.LoadIconW.argtypes = [wintypes.HINSTANCE, ctypes.c_void_p]
            user32.LoadIconW.restype = wintypes.HICON
            icon = user32.LoadIconW(None, IDI_APPLICATION)
            nid = self._nid(hwnd, flags=NIF_MESSAGE | NIF_ICON | NIF_TIP)
            nid.uCallbackMessage = WM_TRAY
            nid.hIcon = icon
            nid.szTip = "Sentinel Lock"
            if not shell32.Shell_NotifyIconW(NIM_ADD, ctypes.byref(nid)):
                raise ctypes.WinError(ctypes.get_last_error())

            self._ready.set()
            message = wintypes.MSG()
            while user32.GetMessageW(ctypes.byref(message), None, 0, 0) > 0:
                user32.TranslateMessage(ctypes.byref(message))
                user32.DispatchMessageW(ctypes.byref(message))
        except BaseException as exc:
            self._start_error = exc
            if self._ready.is_set():
                self._logger.exception("Native system tray stopped unexpectedly")
        finally:
            hwnd = self._hwnd
            self._hwnd = None
            if hwnd is not None and os.name == "nt":
                try:
                    shell32 = ctypes.WinDLL("shell32", use_last_error=True)
                    nid = self._nid(hwnd, flags=0)
                    shell32.Shell_NotifyIconW(NIM_DELETE, ctypes.byref(nid))
                except Exception:
                    self._logger.debug("Tray icon cleanup failed", exc_info=True)
            self._thread_id = None
            self._ready.set()

    def _show_menu(self, hwnd: int) -> None:
        user32 = ctypes.WinDLL("user32", use_last_error=True)
        menu = user32.CreatePopupMenu()
        if not menu:
            return
        try:
            status = self._status_provider()[:120]
            user32.AppendMenuW(menu, MF_STRING | MF_GRAYED, CMD_STATUS, status)
            user32.AppendMenuW(menu, MF_STRING, CMD_LOCK_NOW, "Lock now")
            user32.AppendMenuW(menu, MF_SEPARATOR, 0, None)
            user32.AppendMenuW(menu, MF_STRING, CMD_EXIT, "Exit")
            point = POINT()
            user32.GetCursorPos(ctypes.byref(point))
            user32.SetForegroundWindow(hwnd)
            command = user32.TrackPopupMenu(
                menu,
                TPM_RETURNCMD | TPM_NONOTIFY,
                point.x,
                point.y,
                0,
                hwnd,
                None,
            )
            if command == CMD_LOCK_NOW:
                self._lock_now()
            elif command == CMD_EXIT:
                self._exit_app()
                user32.DestroyWindow(hwnd)
        finally:
            user32.DestroyMenu(menu)

    @staticmethod
    def _nid(hwnd: int, *, flags: int) -> NOTIFYICONDATAW:
        nid = NOTIFYICONDATAW()
        nid.cbSize = ctypes.sizeof(NOTIFYICONDATAW)
        nid.hWnd = hwnd
        nid.uID = 1
        nid.uFlags = flags
        return nid
