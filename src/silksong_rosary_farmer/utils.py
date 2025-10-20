"""
General utilities
"""

import os
from collections.abc import Callable

from pynput.keyboard import Key, Listener


def hex_to_rgb(hex_color) -> tuple[int, int, int]:
    """Convert hex color string to RGB tuple"""

    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))


def setup_escape_exit(
    release_keys_func: Callable[[], None] | None = None,
):
    """Start a background listener that exits the process on Esc.

    If provided, ``release_keys_func`` will be called before exiting to release any
    potentially pressed keys (useful when automating keyboard input).
    """

    def on_press(key):
        if key == Key.esc:
            print("\n🛑 Esc detected - stopping...")
            try:
                if release_keys_func is not None:
                    release_keys_func()
            except Exception:
                pass
            os._exit(0)

    listener = Listener(on_press=on_press)
    listener.start()
    print("🎮 Press Esc to stop the script")
    return listener
