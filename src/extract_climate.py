
from pathlib import Path
import time

import requests
import pandas as pd
import numpy as np


# ==================================================
# GEOANALOG - NASA POWER
# Extraccion de variables climaticas y solares
# ==================================================

BASE_DIR = Path(__file__).resolve().parent.parent

OUTPUT_DIR = BASE_DIR / "data" / "features"
RAW_DIR = BASE_DIR / "data" / "raw" / "climate"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
RAW_DIR.mkdir(parents=True, exist_ok=True)

START = "20210101"
END = "20251231"

API = (
    "https://power.larc.nasa.gov"
    "/api/temporal/daily/point"
)


# 1. REGIONES DE ESTUDIO
# ==================================================

LOCATIONS = {
    "Tatacoa": (3.2300, -75.1700),
    "La_Guajira": (12.43653, -71.60899),
    "Nevado_del_Ruiz": (4.8950, -75.3220),
    "Volcan_Purace": (2.3095, -76.3948),
    "La_Candelaria": (5.5368, -73.6163),
    "Nevado_Santa_Isabel": (4.8180, -75.3650)
}


# 2. VARIABLES CLIMATICAS
# ==================================================

PARAMETERS = [
    "T2M",
    "T2M_MAX",
    "T2M_MIN",
    "RH2M",
    "PS",
    "WS10M",
    "ALLSKY_SFC_SW_DWN",
    "GWETTOP"
]


# 3. EXTRACCION DE DATOS
# ==================================================

def extract_climate(region, lat, lon):

    params = {
        "parameters": ",".join(PARAMETERS),
        "community": "RE",
        "latitude": lat,
        "longitude": lon,
        "start": START,
        "end": END,
        "format": "JSON"
    }

    response = requests.get(
        API,
        params=params,
        timeout=180
    )

    response.raise_for_status()

    data = response.json()

    values = data["properties"]["parameter"]

    df = pd.DataFrame(values)

    missing = data.get("header", {}).get(
        "fill_value", -999
    )

    df = df.replace(missing, np.nan)
    df = df.replace(-999, np.nan)

    df.index = pd.to_datetime(
        df.index,
        format="%Y%m%d"
    )

    df.index.name = "date"

    # Guardar la serie temporal original
    df.to_csv(
        RAW_DIR / f"{region}_NASA_POWER.csv"
    )

    # Unidad de radiacion reportada por la API
    solar_unit = data.get(
        "parameters", {}
    ).get(
        "ALLSKY_SFC_SW_DWN", {}
    ).get("units", "unknown")

    delta = df["T2M_MAX"] - df["T2M_MIN"]

    # Estadisticas climaticas
    features = {
        "region": region,
        "planet": "earth",

        "latitude": lat,
        "longitude": lon,

        "climate_period_start": START,
        "climate_period_end": END,

        "air_temperature_mean_c":
            df["T2M"].mean(),

        "air_temperature_daily_max_mean_c":
            df["T2M_MAX"].mean(),

        "air_temperature_daily_min_mean_c":
            df["T2M_MIN"].mean(),

        "air_temperature_max_c":
            df["T2M_MAX"].max(),

        "air_temperature_min_c":
            df["T2M_MIN"].min(),

        "air_thermal_range_mean_c":
            delta.mean(),

        "relative_humidity_mean_pct":
            df["RH2M"].mean(),

        "surface_pressure_mean_kpa":
            df["PS"].mean(),

        "wind_speed_mean_ms":
            df["WS10M"].mean(),

        "wind_speed_p95_ms":
            df["WS10M"].quantile(0.95),

        "solar_radiation_daily_mean":
            df["ALLSKY_SFC_SW_DWN"].mean(),

        "solar_radiation_unit":
            solar_unit,

        "surface_soil_wetness_mean":
            df["GWETTOP"].mean(),

        "valid_observations_pct":
            100 * df.notna().sum().sum()
            / (1826 * len(PARAMETERS)),

        "climate_source": "NASA POWER"
    }

    return features


# 4. PROCESAMIENTO AUTOMATICO
# ==================================================

results = []

for region, (lat, lon) in LOCATIONS.items():

    print(f"\nProcesando: {region}")

    try:

        features = extract_climate(
            region, lat, lon
        )

        results.append(features)

        print(
            "Temperatura del aire:",
            round(features["air_temperature_mean_c"], 2),
            "C"
        )

        print(
            "Humedad relativa:",
            round(features["relative_humidity_mean_pct"], 2),
            "%"
        )

        print(
            "Presion atmosferica:",
            round(features["surface_pressure_mean_kpa"], 2),
            "kPa"
        )

        print(
            "Radiacion solar:",
            round(features["solar_radiation_daily_mean"], 2),
            features["solar_radiation_unit"]
        )

        print("Estado: OK")

    except Exception as error:

        print(f"ERROR: {error}")

    time.sleep(2)


# 5. EXPORTAR DATASET
# ==================================================

if results:

    df = pd.DataFrame(results)

    output = OUTPUT_DIR / "climate_features.csv"

    df.to_csv(
        output,
        index=False,
        float_format="%.5f"
    )

    print("\nDATASET CLIMATICO GENERADO")
    print("Regiones:", len(df))
    print("Columnas:", len(df.columns))
    print("Archivo:", output)

else:

    print("No se obtuvieron datos climaticos.")
