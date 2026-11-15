
from pathlib import Path

import earthaccess
import pandas as pd


# ==================================================
# GEOANALOG - NASA EMIT
# Busqueda de disponibilidad mineralogica
# ==================================================

BASE_DIR = Path(__file__).resolve().parent.parent

OUTPUT_DIR = BASE_DIR / "data" / "features"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


LOCATIONS = {
    "Tatacoa": (3.2300, -75.1700),
    "La_Guajira": (12.43653, -71.60899),
    "Nevado_del_Ruiz": (4.8950, -75.3220),
    "Volcan_Purace": (2.3095, -76.3948),
    "La_Candelaria": (5.5368, -73.6163),
    "Nevado_Santa_Isabel": (4.8180, -75.3650)
}


results = []

for region, (lat, lon) in LOCATIONS.items():

    print(f"\nBuscando datos EMIT: {region}")

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

        print("Escenas encontradas:", len(granules))

        results.append({
            "region": region,
            "planet": "earth",
            "latitude": lat,
            "longitude": lon,
            "emit_granules": len(granules),
            "emit_available": len(granules) > 0,
            "source": "NASA EMIT L2B"
        })

    except Exception as error:

        print(f"ERROR: {error}")

        results.append({
            "region": region,
            "planet": "earth",
            "latitude": lat,
            "longitude": lon,
            "emit_granules": None,
            "emit_available": None,
            "error": str(error)
        })


df = pd.DataFrame(results)

output = OUTPUT_DIR / "emit_availability.csv"

df.to_csv(output, index=False)

print("\n================================")
print("BUSQUEDA FINALIZADA")
print("================================")
print(df.to_string(index=False))
print("\nArchivo guardado:", output)
