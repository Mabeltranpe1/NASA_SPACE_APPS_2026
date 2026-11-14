
from pathlib import Path

import numpy as np
import rasterio
from rasterio.warp import reproject, Resampling
from rasterio.transform import from_origin


# ==================================================
# GEOANALOG - Homogeneizacion espacial
# ==================================================

BASE_DIR = Path(__file__).resolve().parent.parent

INPUT_DIR = BASE_DIR / "data" / "raw" / "earth"
OUTPUT_DIR = BASE_DIR / "data" / "processed" / "earth"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

TARGET_RESOLUTION = 200  # metros por pixel
REGION_SIZE = 10000     # metros
NODATA = -9999


def resample_dem(input_path, output_path):

    with rasterio.open(input_path) as src:

        # Verificar sistema de coordenadas
        if src.crs is None or not src.crs.is_projected:
            raise ValueError("El DEM requiere una proyeccion metrica.")

        if src.crs.linear_units.lower() not in (
            "metre", "meter", "metres", "meters"
        ):
            raise ValueError("La proyeccion debe utilizar metros.")

        print(f"\nProcesando: {input_path.name}")
        print(f"Resolucion original: {src.res}")
        print(f"Dimensiones originales: {src.width} x {src.height}")
        print(f"Proyeccion: {src.crs}")

        if max(src.res) > TARGET_RESOLUTION * 1.001:
            raise ValueError("La resolucion original es demasiado gruesa.")

        # Leer elevaciones y respetar valores NoData
        source = src.read(1, masked=True)
        source = source.astype("float32").filled(NODATA)

        source[~np.isfinite(source)] = NODATA

        # Centro de la region original
        center_x = (src.bounds.left + src.bounds.right) / 2
        center_y = (src.bounds.top + src.bounds.bottom) / 2

        # Crear una cuadricula de 10 x 10 km
        left = center_x - REGION_SIZE / 2
        top = center_y + REGION_SIZE / 2

        width = int(REGION_SIZE / TARGET_RESOLUTION)
        height = int(REGION_SIZE / TARGET_RESOLUTION)

        transform = from_origin(
            left,
            top,
            TARGET_RESOLUTION,
            TARGET_RESOLUTION
        )

        destination = np.full(
            (height, width),
            NODATA,
            dtype=np.float32
        )

        # Remuestreo por promedio
        reproject(
            source=source,
            destination=destination,

            src_transform=src.transform,
            src_crs=src.crs,
            src_nodata=NODATA,

            dst_transform=transform,
            dst_crs=src.crs,
            dst_nodata=NODATA,

            resampling=Resampling.average
        )

        # Configuracion del nuevo GeoTIFF
        profile = {
            "driver": "GTiff",
            "height": height,
            "width": width,
            "count": 1,
            "dtype": "float32",
            "crs": src.crs,
            "transform": transform,
            "nodata": NODATA,
            "compress": "lzw"
        }

        # Guardar resultado
        with rasterio.open(output_path, "w", **profile) as dst:
            dst.write(destination, 1)

        valid = destination[destination != NODATA]

        print(f"Resolucion final: {TARGET_RESOLUTION} m")
        print(f"Dimensiones finales: {width} x {height}")
        print(f"Pixeles validos: {valid.size}/{width * height}")

        if valid.size > 0:
            print(f"Elevacion minima: {valid.min():.2f} m")
            print(f"Elevacion maxima: {valid.max():.2f} m")
            print(f"Elevacion media: {valid.mean():.2f} m")

        print(f"Archivo guardado: {output_path.name}")


# ==================================================
# PROCESAMIENTO AUTOMATICO
# ==================================================

files = sorted(INPUT_DIR.glob("*.tif"))

if not files:
    print("No se encontraron archivos GeoTIFF.")

for file in files:

    output_file = OUTPUT_DIR / f"{file.stem}_200m.tif"

    try:
        resample_dem(file, output_file)

    except Exception as error:
        print(f"ERROR en {file.name}: {error}")

print("\nProcesamiento finalizado.")
