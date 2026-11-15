"""
terrain_common.py - One way to measure terrain, the same for Earth, Moon and Mars.

Slope and roughness depend on the pixel size: the same mountain looks
steeper and rougher in a 30 m map than in a 200 m map. The Earth maps are
~30-90 m, the Moon map 80 m and the Mars map 200 m, so before measuring
anything we bring every map to the SAME pixel size: 200 m x 200 m (the
coarsest of the three, so no body gets detail that the others lack).

    resample_to_200m(z, px_x, px_y)  -> elevation with 200 m square pixels
    slope_and_roughness(z)           -> slope (degrees) and roughness (m),
                                        both measured between 200 m pixels

Roughness = standard deviation of elevation in a 3 x 3 window (600 m wide).
"""

import numpy as np
from scipy.ndimage import uniform_filter, zoom

PIXEL_M = 200.0   # the common pixel size for every body


def _fill_nan(z):
    """Replace empty pixels by the mean, so filters do not spread NaN."""
    mask = np.isnan(z)
    if mask.all():
        return np.zeros_like(z), mask
    return np.where(mask, np.nanmean(z), z), mask


def resample_to_200m(z, px_x, px_y):
    """
    Bring an elevation map with pixels of px_x by px_y metres to 200 m pixels.
    First average the small pixels over a 200 m window (so detail is averaged,
    not just skipped), then sample the result every 200 m.
    Returns (z_200m, empty_mask_200m).
    """
    filled, mask = _fill_nan(np.asarray(z, dtype=float))
    window = (max(1, int(round(PIXEL_M / px_y))), max(1, int(round(PIXEL_M / px_x))))
    smooth = uniform_filter(filled, size=window, mode="nearest")
    factors = (px_y / PIXEL_M, px_x / PIXEL_M)
    z200 = zoom(smooth, factors, order=1, mode="nearest")
    mask200 = zoom(mask.astype(float), factors, order=1, mode="nearest") > 0.5
    z200[mask200] = np.nan
    return z200, mask200


def slope_and_roughness(z200):
    """Slope (degrees) and roughness (m) of a map that already has 200 m pixels."""
    filled, mask = _fill_nan(z200)
    dz_dy, dz_dx = np.gradient(filled, PIXEL_M, PIXEL_M)
    slope = np.degrees(np.arctan(np.hypot(dz_dx, dz_dy)))
    mean = uniform_filter(filled, 3, mode="nearest")
    rough = np.sqrt(np.clip(uniform_filter(filled**2, 3, mode="nearest") - mean**2, 0, None))
    slope[mask] = np.nan
    rough[mask] = np.nan
    return slope, rough


def pixel_offsets_km(shape):
    """
    For a square window centred on a site: distance of every pixel centre
    from the centre, in km (dy, dx). Used to pick the pixels inside a site.
    """
    rows, cols = shape
    dy = (np.arange(rows) - (rows - 1) / 2) * PIXEL_M / 1000
    dx = (np.arange(cols) - (cols - 1) / 2) * PIXEL_M / 1000
    return np.meshgrid(dy, dx, indexing="ij")
