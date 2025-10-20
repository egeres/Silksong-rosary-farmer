"""
Image processing utilities
"""

import numpy as np


def img_2_color_centroid(img_array, color_rgb, tolerance) -> tuple[float, float] | None:
    """Find the centroid of pixels matching the target color"""

    diff = np.abs(img_array.astype(np.int16) - np.array(color_rgb, dtype=np.int16))
    mask = np.max(diff, axis=2) <= tolerance
    if np.any(mask):
        match_y, match_x = np.where(mask)
        centroid_x = np.mean(match_x)
        centroid_y = np.mean(match_y)
        height, width = mask.shape
        normalized_x = centroid_x / (width - 1) if width > 1 else 0.5
        normalized_y = centroid_y / (height - 1) if height > 1 else 0.5
        return (normalized_x, normalized_y)
    return None


def img_2_coloravg(img_array) -> tuple[float, float, float, float]:
    """Returns the average R, G, B, and the sum"""

    a = np.mean(img_array, axis=(0, 1))
    added_together = np.sum(a)
    return (int(a[0]), int(a[1]), int(a[2]), added_together)


def color_2_room_is_loading(color) -> bool:
    """Check if room is loading, basically, if the image is black 🤷🏻‍♂️"""

    _r, _g, _b, w = color
    return w < 30
