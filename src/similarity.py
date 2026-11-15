
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


# ==================================================
# GEOANALOG - Planetary Analog Index (PAI)
# ==================================================

BASE_DIR = Path(__file__).resolve().parent.parent

INPUT_FILE = (
    BASE_DIR / "data" / "features"
    / "planetary_features.csv"
)

OUTPUT_DIR = BASE_DIR / "data" / "results"


# ==================================================
# 1. VARIABLES Y PONDERACIONES
# ==================================================

FEATURES = [
    "relief_p90_p10_m",
    "elevation_std_m",
    "slope_mean_deg",
    "slope_p90_deg",
    "tri_mean_m",
    "tpi_std_m"
]

WEIGHTS = np.array([
    0.15,  # Relieve
    0.15,  # Variabilidad de elevacion
    0.15,  # Pendiente promedio
    0.15,  # Pendiente P90
    0.15,  # TRI
    0.25   # TPI
])


# ==================================================
# 2. CARGAR DATASET
# ==================================================


def calculate_similarity(a, b, weights=WEIGHTS):

    distance = np.sqrt(
        np.sum(weights * (a - b) ** 2)
    )

    pai = 100 / (1 + distance)

    return distance, pai


def main(input_file=INPUT_FILE, output_dir=OUTPUT_DIR):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(input_file)

    df = df.dropna(subset=FEATURES).copy()

    df["region_id"] = (
        df["planet"] + "_" + df["region"]
    )

    df = df.set_index("region_id")

    earth = df[df["planet"] == "earth"].copy()

    if len(earth) < 2:
        raise ValueError(
            "Se necesitan al menos dos regiones terrestres."
        )

    print("Regiones disponibles:", len(df))
    print("Regiones terrestres:", len(earth))


    # ==================================================
    # 3. NORMALIZACION Z-SCORE
    # ==================================================

    mean = earth[FEATURES].mean()
    std = earth[FEATURES].std(ddof=0)

    # Excluir variables sin variabilidad
    active = std > 1e-10

    if not active.any():
        raise ValueError("No existen variables con variabilidad.")

    features = [
        f for f in FEATURES if active[f]
    ]

    weights = WEIGHTS[active.to_numpy()]
    weights = weights / weights.sum()

    normalized = (
        df[features] - mean[features]
    ) / std[features]

    normalized.to_csv(
        output_dir / "normalized_features.csv"
    )

    # Guardar parametros de normalizacion
    pd.DataFrame({
        "mean": mean,
        "std": std,
        "active": active
    }).to_csv(
        output_dir / "normalization_parameters.csv"
    )


    # ==================================================
    # 4. FUNCION DE SIMILITUD
    # ==================================================



    # ==================================================
    # 5. MATRIZ DE SIMILITUD
    # ==================================================

    names = normalized.index.tolist()

    matrix = np.zeros(
        (len(names), len(names))
    )

    for i, name_a in enumerate(names):

        for j, name_b in enumerate(names):

            a = normalized.loc[name_a].to_numpy()
            b = normalized.loc[name_b].to_numpy()

            distance, pai = calculate_similarity(a, b, weights)

            matrix[i, j] = pai


    similarity_df = pd.DataFrame(
        matrix,
        index=names,
        columns=names
    )

    similarity_df.to_csv(
        output_dir / "similarity_matrix.csv"
    )


    # ==================================================
    # 6. VISUALIZAR MATRIZ
    # ==================================================

    fig, ax = plt.subplots(figsize=(10, 8))

    im = ax.imshow(
        matrix,
        cmap="viridis",
        vmin=0,
        vmax=100
    )

    ax.set_xticks(range(len(names)))
    ax.set_yticks(range(len(names)))

    ax.set_xticklabels(
        names,
        rotation=45,
        ha="right"
    )

    ax.set_yticklabels(names)

    if len(names) <= 20:

        for i in range(len(names)):

            for j in range(len(names)):

                ax.text(
                    j, i,
                    f"{matrix[i, j]:.1f}",
                    ha="center",
                    va="center",
                    color=(
                        "black"
                        if matrix[i, j] > 65
                        else "white"
                    )
                )

    fig.colorbar(im, label="Planetary Analog Index")

    ax.set_title("GeoAnalog - Similarity Matrix")

    plt.tight_layout()

    plt.savefig(
        output_dir / "similarity_matrix.png",
        dpi=200
    )

    plt.close(fig)


    # ==================================================
    # 7. BUSCAR ANALOGOS TERRESTRES
    # ==================================================

    planetary = df[
        df["planet"].isin(["mars", "moon"])
    ]

    if planetary.empty:

        # Prueba entre regiones terrestres
        targets = earth

        print(
            "\nModo de prueba: comparacion terrestre."
        )

    else:

        targets = planetary

        print(
            "\nModo de busqueda planetaria."
        )


    results = []

    for target_id in targets.index:

        for candidate_id in earth.index:

            if target_id == candidate_id:
                continue

            a = normalized.loc[target_id].to_numpy()
            b = normalized.loc[candidate_id].to_numpy()

            distance, pai = calculate_similarity(a, b, weights)

            results.append({

                "target": target_id,
                "candidate": candidate_id,
                "distance": distance,
                "PAI": pai

            })


    ranking = pd.DataFrame(results)

    ranking = ranking.sort_values(
        ["target", "PAI"],
        ascending=[True, False]
    )

    ranking.to_csv(
        output_dir / "analog_ranking.csv",
        index=False,
        float_format="%.5f"
    )


    # ==================================================
    # 8. MOSTRAR RESULTADOS
    # ==================================================

    for target, group in ranking.groupby("target"):

        print("\n================================")
        print("Region objetivo:", target)
        print("================================")

        print(
            group[["candidate", "PAI"]]
            .head(5)
            .to_string(index=False)
        )

    print("\nProcesamiento finalizado.")
    print("Resultados guardados en:", output_dir)


if __name__ == "__main__":
    main()
