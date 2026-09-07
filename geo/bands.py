
import numpy as np


def select_rgb_bands(
    data: np.ndarray,
    rgb_bands: tuple[int, int, int]
) -> np.ndarray:
    """
    Select three bands from a band-first satellite array.

    Parameters
    ----------
    data:
        Array with shape (bands, height, width).

    rgb_bands:
        Three 1-based band numbers to use as
        Red, Green and Blue.

    Returns
    -------
    np.ndarray
        RGB array with shape (height, width, 3).
    """

    if data.ndim != 3:
        raise ValueError(
            "Expected band-first data with shape "
            "(bands, height, width)."
        )

    band_count = data.shape[0]

    for band in rgb_bands:
        if band < 1 or band > band_count:
            raise ValueError(
                f"Band {band} is not available. "
                f"Image contains {band_count} band(s)."
            )

    red = data[rgb_bands[0] - 1]
    green = data[rgb_bands[1] - 1]
    blue = data[rgb_bands[2] - 1]

    rgb = np.stack(
        [red, green, blue],
        axis=-1
    )

    return rgb
