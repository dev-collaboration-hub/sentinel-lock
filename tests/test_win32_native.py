import os
import unittest


@unittest.skipUnless(os.name == "nt", "Win32 ctypes adapters require Windows")
class Win32NativeAdapterTests(unittest.TestCase):
    def test_keyboard_hook_maps_keydown_without_key_payload(self) -> None:
        from sentinel_lock.win32_input import WM_KEYDOWN, Win32KeyboardListener

        received: list[object] = []
        listener = Win32KeyboardListener(on_press=received.append)
        listener._handle_message(WM_KEYDOWN)

        self.assertEqual(received, [None])

    def test_mouse_hook_discards_coordinates_and_button_identity(self) -> None:
        from sentinel_lock.win32_input import (
            WM_LBUTTONDOWN,
            WM_MOUSEMOVE,
            Win32MouseListener,
        )

        moves: list[tuple[int, int]] = []
        clicks: list[tuple[int, int, object, bool]] = []
        listener = Win32MouseListener(
            on_move=lambda x, y: moves.append((x, y)),
            on_click=lambda x, y, button, pressed: clicks.append(
                (x, y, button, pressed)
            ),
        )
        listener._handle_message(WM_MOUSEMOVE)
        listener._handle_message(WM_LBUTTONDOWN)

        self.assertEqual(moves, [(0, 0)])
        self.assertEqual(clicks, [(0, 0, None, True)])

    def test_native_tray_backend_imports_without_third_party_modules(self) -> None:
        from sentinel_lock.win32_tray import Win32TrayBackend

        backend = Win32TrayBackend(
            status_provider=lambda: "active",
            lock_now=lambda: None,
            exit_app=lambda: None,
        )
        self.assertIsNotNone(backend)


if __name__ == "__main__":
    unittest.main()
