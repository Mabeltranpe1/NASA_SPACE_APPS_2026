
from pathlib import Path

import earthaccess
import pandas as pd


# ==================================================
# GEOANALOG - NASA EMIT
# Descarga de datos mineralogicos
# ==================================================

BASE_DIR = Path(__file__).resolve().parent.parent

RAW_DIR = BASE_DIR / "data" / "raw" / "emit"
OUTPUT_DIR = BASE_DIR / "data" / "features"

RAW_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

MAX_SCENES = 3

LOCATIONS = {
    "Tatacoa": (3.2300, -75.1700),
    "La_Guajira": (12.43653, -71.60899),
    "Nevado_del_Ruiz": (4.8950, -75.3220),
    "Volcan_Purace": (2.3095, -76.3948),
    "La_Candelaria": (5.5368, -73.6163),
    "Nevado_Santa_Isabel": (4.8180, -75.3650)
}


# 1. AUTENTICACION NASA EARTHDATA
# ==================================================

earthaccess.login(strategy="interactive")

results = []


# 2. BUSQUEDA Y DESCARGA
# ==================================================

for region, (lat, lon) in LOCATIONS.items():

    print(f"\n========== {region} ==========")

    region_dir = RAW_DIR / region

    region_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    try:

        granules = earthaccess.search_data(

            short_name="EMITL2BMIN",
            version="001",

            temporal=(
                "2022-08-09",
                "2026-11-14"
            ),

            bounding_box=(
                lon - 0.05,
                lat - 0.05,
                lon + 0.05,
                lat + 0.05
            )
        )

        print("Escenas disponibles:", len(granules))

        # Ordenar por fecha de adquisicion
        granules = sorted(
            granules,
            key=lambda g: g["umm"]
                .get("TemporalExtent", {})
                .get("RangeDateTime", {})
                .get("BeginningDateTime", ""),
            reverse=True
        )

        selected = granules[:MAX_SCENES]

        print("Escenas seleccionadas:", len(selected))

        if not selected:
            continue

        for granule in selected:

            print(
                "Granulo:",
                granule["umm"].get("GranuleUR")
            )

        downloaded = earthaccess.download(
            selected,
            str(region_dir)
        )

        nc_files = list(region_dir.glob("*.nc"))

        print("Archivos NetCDF en carpeta:", len(nc_files))

        results.append({

            "region": region,
            "available_granules": len(granules),
            "selected_granules": len(selected),
            "local_nc_files": len(nc_files),
            "source": "NASA EMIT L2B V001"

        })

    except Exception as error:

        print("ERROR:", error)

        results.append({
            "region": region,
            "error": str(error)
        })


# 3. GUARDAR REGISTRO DE DESCARGAS
# ==================================================

df = pd.DataFrame(results)

output = OUTPUT_DIR / "emit_downloads.csv"

df.to_csv(output, index=False)

print("\n================================")
print("DESCARGA FINALIZADA")
print("================================")
print(df.to_string(index=False))
print("\nRegistro:", output)
