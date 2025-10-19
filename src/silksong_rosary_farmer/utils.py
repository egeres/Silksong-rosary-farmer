"""
General utilities
"""


def hex_to_rgb(hex_color) -> tuple[int, int, int]:
    """Convert hex color string to RGB tuple"""

    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))
