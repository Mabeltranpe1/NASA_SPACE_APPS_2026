
from pathlib import Path

import rasterio
import numpy as np
import matplotlib.pyplot as plt

BASE_DIR = Path(__file__).resolve().parent.parent

region = "Tatacoa"

original_path = (
    BASE_DIR / "data" / "raw" / "earth"
    / f"{region}_DEM.tif"
)

processed_path = (
    BASE_DIR / "data" / "processed" / "earth"
    / f"{region}_DEM_200m.tif"
)


def read_dem(path):

    with rasterio.open(path) as src:

        data = src.read(1, masked=True)
        data = data.astype(float).filled(np.nan)

        return data, src.res


original, original_res = read_dem(original_path)
processed, processed_res = read_dem(processed_path)

# Misma escala de colores
vmin = min(np.nanmin(original), np.nanmin(processed))
vmax = max(np.nanmax(original), np.nanmax(processed))

fig, axes = plt.subplots(
    1, 2,
    figsize=(12, 6),
    constrained_layout=True
)

axes[0].imshow(
    original,
    cmap="terrain",
    vmin=vmin,
    vmax=vmax,
    interpolation="nearest"
)

axes[0].set_title(
    f"DEM Original\n{original_res[0]:.0f} m/pixel\n"
    f"{original.shape[1]} x {original.shape[0]}"
)

im = axes[1].imshow(
    processed,
    cmap="terrain",
    vmin=vmin,
    vmax=vmax,
    interpolation="nearest"
)

axes[1].set_title(
    f"DEM Homogeneizado\n{processed_res[0]:.0f} m/pixel\n"
    f"{processed.shape[1]} x {processed.shape[0]}"
)

for ax in axes:
    ax.set_xlabel("Pixel X")
    ax.set_ylabel("Pixel Y")

fig.colorbar(im, ax=axes, label="Elevacion (m)")

fig.suptitle(
    f"GeoAnalog - {region}",
    fontsize=16
)

plt.show()
