
from pathlib import Path

import numpy as np
import rasterio

from rasterio.warp import reproject, Resampling
from rasterio.transform import from_origin
from rasterio.crs import CRS
from pyproj import CRS as ProjCRS


# ==================================================
# GEOANALOG - Procesamiento de Marte y la Luna
# ==================================================

BASE_DIR = Path(__file__).resolve().parent.parent

RAW_DIR = BASE_DIR / "data" / "raw"
OUTPUT_DIR = BASE_DIR / "data" / "processed"

RESOLUTION = 200
REGION_SIZE = 10000
NODATA = -9999.0

SIZE = REGION_SIZE // RESOLUTION

for planet in ["mars", "moon"]:

    (OUTPUT_DIR / planet).mkdir(
        parents=True,
        exist_ok=True
    )


# ==================================================
# 1. REGIONES DE MARTE
# ==================================================

MARS_FILE = (
    RAW_DIR / "mars"
    / "Mars_HRSC_MOLA_BlendDEM_Global_200mp_v2.tif"
)

MARS_SITES = {
    "Jezero": (18.4447, 77.4508),
    "Gale": (-4.5900, 137.4400),
    "Phoenix": (68.2200, 234.2500),
    "Pathfinder": (19.0950, 326.7470),
    "Viking_1": (22.2690, 312.0490),
    "Viking_2": (47.6680, 134.2800)
}


# ==================================================
# 2. REGIONES DE LA LUNA
# ==================================================

MOON_SITES = {
    "Site01": "Connecting_Ridge",
    "Site04": "Shackleton_Rim",
    "Site07": "Peak_Near_Shackleton",
    "Site11": "De_Gerlache_Rim",
    "Site20": "Leibnitz_Beta_Plateau",
    "Site23": "Malapert_Massif"
}


# ==================================================
# 3. FUNCION GENERAL DE REMUESTREO
# ==================================================

def process_dem(
    src,
    dst_crs,
    center_x,
    center_y,
    output_path
):

    if src.crs is None:
        raise ValueError("El archivo no tiene CRS.")

    transform = from_origin(
        center_x - REGION_SIZE / 2,
        center_y + REGION_SIZE / 2,
        RESOLUTION,
        RESOLUTION
    )

    destination = np.full(
        (SIZE, SIZE),
        np.nan,
        dtype=np.float32
    )

    # Leer directamente desde el archivo.
    # Evita cargar todo Marte en la memoria RAM.

    reproject(
        source=rasterio.band(src, 1),
        destination=destination,

        src_transform=src.transform,
        src_crs=src.crs,
        src_nodata=src.nodata,

        dst_transform=transform,
        dst_crs=dst_crs,
        dst_nodata=np.nan,

        resampling=Resampling.average,
        warp_mem_limit=128
    )

    # Aplicar factores de escala y offset
    # registrados en los metadatos del GeoTIFF.

    scale = src.scales[0]
    offset = src.offsets[0]

    destination = destination * scale + offset

    valid = np.isfinite(destination)

    coverage = 100 * valid.sum() / destination.size

    if coverage < 90:
        raise ValueError(
            f"Cobertura insuficiente: {coverage:.2f}%"
        )

    values = destination[valid]

    destination[~valid] = NODATA

    profile = {
        "driver": "GTiff",
        "height": SIZE,
        "width": SIZE,
        "count": 1,
        "dtype": "float32",
        "crs": dst_crs,
        "transform": transform,
        "nodata": NODATA,
        "compress": "lzw"
    }

    with rasterio.open(
        output_path, "w", **profile
    ) as dst:

        dst.write(destination, 1)

        dst.update_tags(
            elevation_units="m",
            source_dataset=Path(src.name).name,
            target_resolution_m=RESOLUTION
        )

    print(f"Archivo: {output_path.name}")
    print(f"Resolucion: {RESOLUTION} m/pixel")
    print(f"Dimensiones: {SIZE} x {SIZE}")
    print(f"Cobertura valida: {coverage:.2f}%")
    print(f"Elevacion minima: {values.min():.2f} m")
    print(f"Elevacion maxima: {values.max():.2f} m")
    print("Estado: OK")


# ==================================================
# 4. PROCESAR MARTE
# ==================================================

def process_mars():

    if not MARS_FILE.exists():

        print("\nNo se encontro el DEM global de Marte.")
        return

    with rasterio.open(MARS_FILE) as src:

        print("\n========== MARTE ==========")
        print("CRS original:", src.crs)
        print("Resolucion original:", src.res)
        print("NoData:", src.nodata)
        print("Escala:", src.scales)
        print("Offset:", src.offsets)

        if src.crs is None:
            raise ValueError("El DEM de Marte no tiene CRS.")

        source_crs = ProjCRS.from_wkt(
            src.crs.to_wkt()
        )

        ellipsoid = source_crs.ellipsoid

        a = ellipsoid.semi_major_metre
        b = ellipsoid.semi_minor_metre

        for name, (lat, lon) in MARS_SITES.items():

            print(f"\nProcesando Marte: {name}")

            # Convertir longitud al rango -180 a 180
            lon = (lon + 180) % 360 - 180

            # Proyeccion azimutal equidistante local.
            # Utiliza los radios del modelo de Marte.

            local_crs = CRS.from_proj4(
                f"+proj=aeqd "
                f"+lat_0={lat} +lon_0={lon} "
                f"+a={a} +b={b} "
                f"+units=m +no_defs"
            )

            output = (
                OUTPUT_DIR / "mars"
                / f"{name}_DEM_200m.tif"
            )

            try:

                process_dem(
                    src=src,
                    dst_crs=local_crs,
                    center_x=0,
                    center_y=0,
                    output_path=output
                )

            except Exception as error:

                print("ERROR:", error)


# ==================================================
# 5. PROCESAR LA LUNA
# ==================================================

def process_moon():

    print("\n========== LUNA ==========")

    for site, name in MOON_SITES.items():

        path = (
            RAW_DIR / "moon"
            / f"{site}_final_adj_5mpp_surf.tif"
        )

        if not path.exists():

            print(f"No encontrado: {site}")
            continue

        print(f"\nProcesando Luna: {name}")

        try:

            with rasterio.open(path) as src:

                print("CRS original:", src.crs)
                print("Resolucion original:", src.res)
                print("NoData:", src.nodata)
                print("Escala:", src.scales)
                print("Offset:", src.offsets)

                if src.crs is None:
                    raise ValueError("CRS no disponible.")

                if not src.crs.is_projected:
                    raise ValueError(
                        "Se requiere una proyeccion metrica."
                    )

                if src.crs.linear_units.lower() not in (
                    "metre", "meter", "metres", "meters"
                ):
                    raise ValueError(
                        "El CRS debe utilizar metros."
                    )

                width_m = (
                    src.bounds.right - src.bounds.left
                )

                height_m = (
                    src.bounds.top - src.bounds.bottom
                )

                if min(width_m, height_m) < REGION_SIZE:

                    raise ValueError(
                        "La region original es menor a 10 km."
                    )

                center_x = (
                    src.bounds.left + src.bounds.right
                ) / 2

                center_y = (
                    src.bounds.top + src.bounds.bottom
                ) / 2

                output = (
                    OUTPUT_DIR / "moon"
                    / f"{name}_DEM_200m.tif"
                )

                process_dem(
                    src=src,
                    dst_crs=src.crs,
                    center_x=center_x,
                    center_y=center_y,
                    output_path=output
                )

        except Exception as error:

            print("ERROR:", error)


# ==================================================
# 6. EJECUCION PRINCIPAL
# ==================================================

if __name__ == "__main__":

    process_moon()
    process_mars()

    print("\nProcesamiento planetario finalizado.")
