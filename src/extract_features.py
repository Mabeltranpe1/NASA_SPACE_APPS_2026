
from pathlib import Path

import numpy as np
import pandas as pd
import rasterio
import matplotlib.pyplot as plt

from scipy.ndimage import generic_filter


# ==================================================
# GEOANALOG - Extraccion de caracteristicas fisicas
# ==================================================

BASE_DIR = Path(__file__).resolve().parent.parent

INPUT_DIR = BASE_DIR / "data" / "processed"
OUTPUT_DIR = BASE_DIR / "data" / "features"
FIGURES_DIR = BASE_DIR / "data" / "figures"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
FIGURES_DIR.mkdir(parents=True, exist_ok=True)

TARGET_RESOLUTION = 200


# ==================================================
# 1. FUNCIONES MATEMATICAS
# ==================================================

def calculate_tri(window):

    if not np.all(np.isfinite(window)):
        return np.nan

    center = window[4]

    return np.sqrt(
        np.sum((window - center) ** 2)
    )


def calculate_tpi(window):

    if not np.all(np.isfinite(window)):
        return np.nan

    center = window[4]
    neighbors = np.delete(window, 4)

    return center - np.mean(neighbors)


# ==================================================
# 2. EXTRACCION DE CARACTERISTICAS
# ==================================================

def extract_features(path, planet):

    with rasterio.open(path) as src:

        dem = src.read(1, masked=True)
        dem = dem.astype("float64").filled(np.nan)

        dx, dy = src.res

        if src.crs is None or not src.crs.is_projected:
            raise ValueError("Se requiere una proyeccion metrica.")

        if src.crs.linear_units.lower() not in (
            "metre", "meter", "metres", "meters"
        ):
            raise ValueError("La proyeccion debe utilizar metros.")

        if not np.allclose(
            [dx, dy], TARGET_RESOLUTION
        ):
            raise ValueError("El DEM debe tener resolucion de 200 m.")

    dem[~np.isfinite(dem)] = np.nan

    valid = np.isfinite(dem)

    coverage = 100 * valid.sum() / dem.size

    if coverage < 90:
        raise ValueError("Cobertura valida inferior al 90%.")

    # Elevacion relativa
    relative_dem = dem - np.nanmean(dem)

    # Gradiente y pendiente
    gy, gx = np.gradient(dem, dy, dx)

    slope = np.degrees(
        np.arctan(np.hypot(gx, gy))
    )

    # Rugosidad topografica
    tri = generic_filter(
        dem,
        calculate_tri,
        size=3,
        mode="constant",
        cval=np.nan
    )

    # Posicion topografica
    tpi = generic_filter(
        dem,
        calculate_tpi,
        size=3,
        mode="constant",
        cval=np.nan
    )

    # Usar vecindarios completos
    complete = np.isfinite(tri)

    slope[~complete] = np.nan

    # Orientacion respecto al norte de la cuadricula
    aspect = (
        np.degrees(np.arctan2(-gx, gy)) + 360
    ) % 360

    aspect[(slope == 0) | ~complete] = np.nan

    valid_slopes = slope[np.isfinite(slope)]

    if valid_slopes.size == 0:
        raise ValueError("No hay pendientes validas.")

    # Nombre de la region
    region = path.stem.replace("_DEM_200m", "")

    # Estadisticas fisicas
    features = {

        "region": region,
        "planet": planet,

        "resolution_m": dx,
        "valid_coverage_pct": coverage,

        # Elevacion
        "elevation_min_m": np.nanmin(dem),
        "elevation_max_m": np.nanmax(dem),
        "elevation_mean_m": np.nanmean(dem),
        "elevation_median_m": np.nanmedian(dem),
        "elevation_std_m": np.nanstd(dem),

        # Relieve
        "local_relief_m":
            np.nanmax(dem) - np.nanmin(dem),

        "relief_p90_p10_m":
            np.nanpercentile(dem, 90)
            - np.nanpercentile(dem, 10),

        # Pendiente
        "slope_mean_deg": np.nanmean(slope),
        "slope_median_deg": np.nanmedian(slope),
        "slope_std_deg": np.nanstd(slope),
        "slope_max_deg": np.nanmax(slope),
        "slope_p90_deg": np.nanpercentile(slope, 90),

        # Distribucion de pendientes
        "flat_terrain_pct":
            100 * np.mean(valid_slopes < 5),

        "moderate_terrain_pct":
            100 * np.mean(
                (valid_slopes >= 5)
                & (valid_slopes < 15)
            ),

        "steep_terrain_pct":
            100 * np.mean(valid_slopes >= 15),

        # Rugosidad
        "tri_mean_m": np.nanmean(tri),
        "tri_std_m": np.nanstd(tri),
        "tri_p90_m": np.nanpercentile(tri, 90),

        # Posicion topografica
        "tpi_mean_m": np.nanmean(tpi),
        "tpi_std_m": np.nanstd(tpi),

        "tpi_abs_mean_m":
            np.nanmean(np.abs(tpi))
    }

    # Guardar visualizaciones
    create_figure(
        region,
        planet,
        dem,
        relative_dem,
        slope,
        tri,
        tpi,
        aspect
    )

    return features


# ==================================================
# 3. VISUALIZACION CIENTIFICA
# ==================================================

def create_figure(
    region, planet, dem, relative_dem,
    slope, tri, tpi, aspect
):

    fig, axes = plt.subplots(
        2, 3,
        figsize=(16, 10),
        constrained_layout=True
    )

    layers = [

        (dem, "Elevacion absoluta (m)", "terrain"),
        (relative_dem, "Elevacion relativa (m)", "RdBu_r"),
        (slope, "Pendiente (grados)", "YlOrRd"),
        (tri, "Rugosidad TRI (m)", "magma"),
        (tpi, "Posicion topografica TPI (m)", "coolwarm"),
        (aspect, "Orientacion (grados)", "twilight")
    ]

    for ax, (data, title, cmap) in zip(
        axes.flat, layers
    ):

        options = {}

        if title.startswith("Orientacion"):
            options = {"vmin": 0, "vmax": 360}

        im = ax.imshow(
            data,
            cmap=cmap,
            interpolation="nearest",
            extent=[0, 10, 0, 10],
            **options
        )

        ax.set_title(title)
        ax.set_xlabel("Distancia (km)")
        ax.set_ylabel("Distancia (km)")
        ax.set_aspect("equal")

        fig.colorbar(im, ax=ax, shrink=0.75)

    fig.suptitle(
        f"GeoAnalog | {region} | {planet.upper()}",
        fontsize=18
    )

    output_path = (
        FIGURES_DIR / f"{planet}_{region}_analysis.png"
    )

    fig.savefig(output_path, dpi=200)

    plt.close(fig)


# ==================================================
# 4. PROCESAMIENTO AUTOMATICO
# ==================================================

results = []

for planet in ["earth", "mars", "moon"]:

    planet_dir = INPUT_DIR / planet

    files = sorted(
        planet_dir.glob("*.tif")
    )

    for file in files:

        print(f"\nProcesando: {file.name}")

        try:

            features = extract_features(
                file, planet
            )

            results.append(features)

            print(
                f"Pendiente promedio: "
                f"{features['slope_mean_deg']:.2f} grados"
            )

            print(
                f"Rugosidad promedio: "
                f"{features['tri_mean_m']:.2f} m"
            )

            print(
                f"Relieve local: "
                f"{features['local_relief_m']:.2f} m"
            )

            print("Estado: OK")

        except Exception as error:

            print(f"ERROR: {error}")


# ==================================================
# 5. CREACION DEL DATASET
# ==================================================

if results:

    df = pd.DataFrame(results)

    output_csv = (
        OUTPUT_DIR / "planetary_features.csv"
    )

    df.to_csv(
        output_csv,
        index=False,
        float_format="%.5f"
    )

    print("\nDATASET GENERADO CORRECTAMENTE")
    print(f"Regiones procesadas: {len(df)}")
    print(f"Columnas: {len(df.columns)}")
    print(f"Archivo: {output_csv}")

else:

    print("No se encontraron regiones validas.")
