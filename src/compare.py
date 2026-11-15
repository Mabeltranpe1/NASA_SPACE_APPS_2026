"""
compare.py - Similarity index between Earth grid cells and Moon/Mars sites.

Idea in one sentence:
    Put every place (Earth cells and Moon/Mars targets) on the same scale,
    measure how far each Earth cell is from each target, and turn that
    distance into a score between 0 and 1 (1 = identical, 0 = very different).

Inputs (CSV files, lines starting with '#' are comments and are ignored):
    earth file   : lat, lon, + feature columns   (one row per Earth grid cell)
    targets file : name, body, + feature columns (one row per Moon/Mars site)

Output: one table with, for every (target, Earth cell) pair:
    score       -> overall similarity (0..1)
    sim_<feat>  -> similarity for each single feature (0..1)
    best_match  -> the feature where this cell is MOST like the target
    worst_match -> the feature where the analogy BREAKS
The sim_* / best / worst columns explain WHY a cell got its score.

Examples:
    python src/compare.py --earth data/sample_earth.csv \
                          --targets data/sample_targets.csv --top 5

    # switch one feature off and save everything to a file
    python src/compare.py --weight elev_m=0 --out results.csv

    # check if the ranking is stable when the weights change a little
    python src/compare.py --sensitivity 200
"""

import argparse
import gzip
import sys
import warnings

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# 1. Settings (the part you will edit most often)
# ---------------------------------------------------------------------------

# The features (columns) we compare. Same names in both CSV files.
FEATURES = [
    "elev_m",        # elevation (m)
    "slope_deg",     # terrain slope (degrees)
    "roughness",     # terrain roughness (unitless)
    "temp_mean_K",   # mean surface temperature (Kelvin)
    "temp_range_K",  # day-night / seasonal temperature range (Kelvin)
    "albedo",        # how much sunlight the surface reflects (0..1)
    "precip_mm",     # yearly precipitation (mm)
    "ndvi",          # vegetation index (about 0 = no plants)
    "em_contrast",   # rock type from thermal emissivity (big = silica-rich, small = basalt)
]

# How important each feature is. Bigger number = matters more.
# Set a weight to 0 to switch a feature off completely.
DEFAULT_WEIGHTS = {
    "elev_m": 0.5,   # low: elevation uses a different zero level on each body
    "slope_deg": 1.0,
    "roughness": 1.0,
    "temp_mean_K": 1.5,
    "temp_range_K": 1.0,
    "albedo": 1.0,
    "precip_mm": 1.0,
    "ndvi": 1.0,
    "em_contrast": 1.0,   # Moon/Mars values are calibrated estimates (src/composition.py)
}

# Optional different weights for one body only. They replace DEFAULT_WEIGHTS
# for targets of that body. Example: {"Moon": {"precip_mm": 0.0}}
BODY_WEIGHTS = {}

# Features compared on a logarithmic scale. Rain goes from 0 to thousands of
# mm, and the step from 2 mm to 50 mm (desert -> not desert) matters much
# more than the step from 2000 to 2050 mm. log(1 + x) makes that true.
LOG_FEATURES = ["precip_mm"]

# How big a difference is "a lot" for each feature (used by the default
# "tolerance" scaling). A difference of exactly this size gives that
# feature a similarity of exp(-1) = 0.37; half of it gives 0.61.
# These are physical choices you can defend in front of the judges.
TOLERANCE = {
    "elev_m": 1000.0,      # 1 km of height
    "slope_deg": 5.0,      # 5 degrees of slope
    "roughness": 5.0,      # 5 m of local height variation
    "temp_mean_K": 30.0,   # 30 K of mean temperature
    "temp_range_K": 30.0,  # 30 K of temperature swing
    "albedo": 0.10,        # 0.10 of reflectance
    "precip_mm": 1.0,      # in log scale: about 2.7 times more or less rain
    "ndvi": 0.10,          # 0.10 of vegetation index (bare rock ~0, shrubs ~0.2)
    "em_contrast": 0.03,   # 0.03 of emissivity contrast (basalt ~0.00, andesite ~0.05, quartz sand ~0.15-0.2)
}

# Values outside these limits are probably a unit mistake (e.g. Celsius
# instead of Kelvin). We only print a warning; we do not stop.
VALID_RANGES = {
    "lat": (-90, 90),
    "lon": (-180, 360),
    "slope_deg": (0, 90),
    "roughness": (0, None),
    "temp_mean_K": (20, 400),
    "temp_range_K": (0, 400),
    "albedo": (0, 1),
    "precip_mm": (0, None),
    "ndvi": (-1, 1),
    "em_contrast": (-0.2, 0.5),
}


# ---------------------------------------------------------------------------
# 2. Loading and checking data
# ---------------------------------------------------------------------------

def warn(message):
    """Print a warning without mixing it with the results (goes to stderr)."""
    print(f"WARNING: {message}", file=sys.stderr)


def load_table(path, id_columns):
    """
    Read a CSV and check it before we use it.

    Stops with a clear error when the file cannot be used (missing columns,
    text where a number should be, no rows). Prints a warning when values
    look suspicious but the file can still be used.
    """
    opener = gzip.open if str(path).endswith(".gz") else open   # data/earth_all.csv.gz is compressed
    with opener(path, "rt", encoding="utf-8") as f:
        if "SYNTHETIC" in f.readline().upper():
            warn(f"{path} is SYNTHETIC sample data. The results are not real.")

    df = pd.read_csv(path, comment="#", skipinitialspace=True)
    df.columns = df.columns.str.strip()

    missing = [c for c in id_columns if c not in df.columns]
    if missing:
        raise ValueError(f"{path} is missing columns: {missing}")
    for col in FEATURES:
        if col not in df.columns:
            # Older files do not have the newer variables. That is fine: an
            # empty column is simply not used (weight 0) for targets.
            warn(f"{path} has no '{col}' column; it is treated as empty.")
            df[col] = np.nan
    if df.empty:
        raise ValueError(f"{path} has no data rows.")

    # Every feature must be a number. Empty cells are allowed (they become NaN).
    for col in FEATURES + [c for c in ("lat", "lon") if c in id_columns]:
        try:
            df[col] = pd.to_numeric(df[col])
        except (ValueError, TypeError):
            raise ValueError(f"{path}: column '{col}' contains text that is not a number.") from None
        if np.isinf(df[col]).any():
            raise ValueError(f"{path}: column '{col}' contains infinite values.")

    for col in FEATURES:
        if df[col].isna().all():
            # Fine for targets (e.g. no rain on the Moon), worth knowing for Earth.
            warn(f"{path}: column '{col}' is completely empty, so it will not be used.")

    for col, (low, high) in VALID_RANGES.items():
        if col not in df.columns:
            continue
        bad = (df[col] < low) if low is not None else pd.Series(False, index=df.index)
        if high is not None:
            bad |= df[col] > high
        if bad.any():
            warn(f"{path}: {int(bad.sum())} value(s) in '{col}' are outside "
                 f"the expected range {low}..{high}. Check the units.")

    return df.reset_index(drop=True)


def load_inputs(earth_path, targets_path):
    """Load both tables and check the things that involve the two of them."""
    earth = load_table(earth_path, ["lat", "lon"])
    targets = load_table(targets_path, ["name", "body"])

    if targets["name"].duplicated().any():
        repeated = targets.loc[targets["name"].duplicated(), "name"].tolist()
        raise ValueError(f"{targets_path}: target names must be unique, repeated: {repeated}")
    if earth.duplicated(["lat", "lon"]).any():
        warn(f"{earth_path}: some lat/lon pairs appear more than once.")
    return earth, targets


# ---------------------------------------------------------------------------
# 3. Weights
# ---------------------------------------------------------------------------

def build_weights(weights=None, body=None, body_weights=None):
    """
    Return the weights as an array in the same order as FEATURES.

    Priority (last one wins): DEFAULT_WEIGHTS -> weights for this body ->
    weights given by the caller (e.g. from the command line).
    """
    body_weights = BODY_WEIGHTS if body_weights is None else body_weights
    merged = {**DEFAULT_WEIGHTS, **body_weights.get(body, {}), **(weights or {})}

    unknown = [name for name in merged if name not in FEATURES]
    if unknown:
        raise ValueError(f"Unknown feature(s) in weights: {unknown}. Choose from {FEATURES}")

    w = np.array([merged[f] for f in FEATURES], dtype=float)
    if not np.all(np.isfinite(w)) or (w < 0).any():
        raise ValueError("Weights must be numbers that are 0 or bigger.")
    return w


def parse_weights(items):
    """Turn ['precip_mm=0', 'albedo=2'] into {'precip_mm': 0.0, 'albedo': 2.0}."""
    weights = {}
    for item in items or []:
        name, sep, value = item.partition("=")
        name = name.strip()
        try:
            weights[name] = float(value)
        except ValueError:
            raise ValueError(f"Bad --weight '{item}'. Write it like: --weight precip_mm=0") from None
        if not sep or name not in FEATURES:
            raise ValueError(f"Bad --weight '{item}'. The feature must be one of {FEATURES}")
    return weights


# ---------------------------------------------------------------------------
# 4. Putting everything on the same scale
# ---------------------------------------------------------------------------

def to_matrix(df):
    """Take the FEATURES of a table as a number array (rows x features)."""
    matrix = np.array(df.reindex(columns=FEATURES), dtype=float)  # missing column -> NaN
    for name in LOG_FEATURES:
        j = FEATURES.index(name)
        if np.nanmin(matrix[:, j], initial=0.0) < 0:
            raise ValueError(f"'{name}' has negative values, but it must be 0 or bigger.")
        matrix[:, j] = np.log1p(matrix[:, j])
    return matrix


def scale_together(earth, targets, method="tolerance"):
    """
    Put Earth and targets on the same scale, so features can be compared.

    method="tolerance" (default): divide every difference by TOLERANCE.
        The ruler is physical ("30 K is a big difference"), so a score of
        0.4 means the same thing for every target and every region.
    method="robust": ONE RobustScaler fitted on Earth and targets together.
        Problem we saw in the first real test: with 80,000 Earth cells and
        a few Moon sites, the ruler is set almost only by Earth. Moon
        temperatures are then "100 rulers away" and every score is ~0.

    Why scale: elevation is in thousands of metres and albedo is between 0
    and 1. Without scaling, elevation would dominate the distance.
    Why RobustScaler: it subtracts the median and divides by the
    interquartile range, so a few extreme places do not distort the scale.
    Why together: Earth, Moon and Mars must be measured with the same ruler.
    Empty cells (NaN) are ignored when fitting and stay empty afterwards.

    Returns (earth_scaled, targets_scaled).
    """
    earth_matrix = to_matrix(earth)
    targets_matrix = to_matrix(targets)
    if method == "tolerance":
        tol = np.array([TOLERANCE[f] for f in FEATURES], dtype=float)
        return earth_matrix / tol, targets_matrix / tol
    if method != "robust":
        raise ValueError(f"Unknown scaling '{method}'. Use 'tolerance' or 'robust'.")
    from sklearn.preprocessing import RobustScaler  # only here: the API and the web export run without scikit-learn
    with warnings.catch_warnings():
        # A column that is empty in BOTH files makes numpy complain. That is
        # fine: the column stays empty and is simply not used.
        warnings.simplefilter("ignore", RuntimeWarning)
        scaler = RobustScaler().fit(np.vstack([earth_matrix, targets_matrix]))
    return scaler.transform(earth_matrix), scaler.transform(targets_matrix)


# ---------------------------------------------------------------------------
# 5. The similarity maths
# ---------------------------------------------------------------------------

def score_cells(earth_scaled, target_scaled, w, min_coverage=1.0):
    """
    Compare ONE target (1D array) with EVERY Earth cell (2D array).

    Returns:
        score : one overall similarity per Earth cell (0..1). NaN if the cell
                misses too much data (see min_coverage).
        sims  : one similarity per Earth cell per feature (0..1). NaN where
                the feature is not used or the value is missing.
    """
    # A feature the target does not have (e.g. rain on the Moon) is off.
    w = np.where(np.isnan(target_scaled), 0.0, w)
    if w.sum() == 0:
        raise ValueError("All weights are 0 for this target; nothing to compare.")

    # Difference between each Earth cell and the target, per feature.
    diff = earth_scaled - target_scaled  # shape: (n_cells, n_features)

    # A missing Earth value gives no information -> weight 0 for that cell only.
    cell_w = np.where(np.isnan(diff), 0.0, w)

    # Per-feature similarity: 1 when equal, goes towards 0 when far apart.
    sims = np.where(cell_w > 0, np.exp(-np.abs(diff)), np.nan)

    # Weighted Euclidean distance. Dividing by the sum of the weights keeps
    # scores comparable between targets that use a different number of features.
    weight_sum = cell_w.sum(axis=1)

    # A cell with missing data must not win just because its bad feature was
    # skipped (we saw this in the first test). By default a cell needs ALL the
    # features the target uses; min_coverage=0.8 would accept 80% of the weight.
    coverage = weight_sum / w.sum()
    weight_sum = np.where(coverage >= min_coverage - 1e-9, weight_sum, np.nan)
    weighted_squares = (cell_w * np.nan_to_num(diff) ** 2).sum(axis=1)
    with np.errstate(invalid="ignore", divide="ignore"):
        dist = np.sqrt(weighted_squares / weight_sum)  # NaN = not enough data

    # Turn distance into a score: distance 0 -> score 1, large distance -> ~0.
    return np.exp(-dist), sims


def best_and_worst(sims):
    """For each cell, name the feature with the highest and lowest similarity."""
    names = np.array(FEATURES)
    no_data = np.isnan(sims).all(axis=1)
    best = names[np.argmax(np.nan_to_num(sims, nan=-1.0), axis=1)]
    worst = names[np.argmin(np.nan_to_num(sims, nan=2.0), axis=1)]
    return np.where(no_data, "", best), np.where(no_data, "", worst)


def compare_all(earth, targets, weights=None, body_weights=None, top=None,
                scaling="tolerance", min_coverage=1.0):
    """
    Compare every target with every Earth cell.

    Returns one long table: one row per (target, Earth cell), sorted so the
    best Earth analog of each target comes first (rank 1).
    Use top=N to keep only the N best cells per target (saves memory when
    the Earth grid is very big).
    """
    earth_scaled, targets_scaled = scale_together(earth, targets, scaling)

    results = []
    # enumerate gives the row POSITION, which is what the scaled array needs.
    for pos, (_, target) in enumerate(targets.iterrows()):
        w = build_weights(weights, target["body"], body_weights)
        try:
            score, sims = score_cells(earth_scaled, targets_scaled[pos], w, min_coverage)
        except ValueError as err:
            raise ValueError(f"Target '{target['name']}': {err}") from None

        # Best first. Cells with no score (NaN) go to the end.
        order = np.argsort(-np.nan_to_num(score, nan=-1.0), kind="stable")
        if top is not None:
            order = order[:top]

        best, worst = best_and_worst(sims[order])
        table = earth.iloc[order].copy()
        table.insert(0, "target", target["name"])
        table.insert(1, "body", target["body"])
        table.insert(2, "rank", np.arange(1, len(order) + 1))
        # Where the target is on the Moon or Mars (if the targets file says so),
        # so a map can show both places side by side.
        if "site_lat" in targets.columns and "site_lon" in targets.columns:
            table.insert(2, "target_lat", target["site_lat"])
            table.insert(3, "target_lon", target["site_lon"])
        # The target's own values, next to the Earth values, so one row tells
        # the whole story: Earth place + its twin on the Moon/Mars + scores.
        for feature in FEATURES:
            table[f"target_{feature}"] = target[feature]
        table["score"] = score[order]
        for j, feature in enumerate(FEATURES):
            table[f"sim_{feature}"] = sims[order, j]
        table["best_match"] = best
        table["worst_match"] = worst
        results.append(table)

    return pd.concat(results, ignore_index=True)


# ---------------------------------------------------------------------------
# 6. Sensitivity check: does the ranking depend too much on the weights?
# ---------------------------------------------------------------------------

def weight_sensitivity(earth, targets, weights=None, body_weights=None,
                       top=5, runs=200, spread=0.5, seed=0,
                       scaling="tolerance", min_coverage=1.0):
    """
    Repeat the ranking many times with randomly changed weights.

    In each run every weight is multiplied by a random factor between
    (1 - spread) and (1 + spread). With spread=0.5 a weight of 1.0 becomes
    something between 0.5 and 1.5. Then we count how often each Earth cell
    is still inside the top N.

    Returns a table with a 'top_share' column: 1.0 means "in the top N in
    every run" (a robust analog); a low value means the cell is only good
    for one particular choice of weights.
    """
    if not 0 <= spread < 1:
        raise ValueError("spread must be between 0 and 1 (for example 0.5).")
    if runs < 1:
        raise ValueError("runs must be at least 1.")

    rng = np.random.default_rng(seed)  # fixed seed -> same result every time
    earth_scaled, targets_scaled = scale_together(earth, targets, scaling)

    results = []
    for pos, (_, target) in enumerate(targets.iterrows()):
        base_w = build_weights(weights, target["body"], body_weights)
        base_score, _ = score_cells(earth_scaled, targets_scaled[pos], base_w, min_coverage)
        base_order = np.argsort(-np.nan_to_num(base_score, nan=-1.0), kind="stable")
        base_rank = np.empty(len(earth), dtype=int)
        base_rank[base_order] = np.arange(1, len(earth) + 1)

        times_in_top = np.zeros(len(earth))
        for _run in range(runs):
            factors = rng.uniform(1 - spread, 1 + spread, size=len(FEATURES))
            score, _ = score_cells(earth_scaled, targets_scaled[pos], base_w * factors, min_coverage)
            order = np.argsort(-np.nan_to_num(score, nan=-1.0), kind="stable")
            times_in_top[order[:top]] += 1

        # Keep the cells that are in the normal top N or entered it at least once.
        keep = base_order[(base_rank[base_order] <= top) | (times_in_top[base_order] > 0)]
        table = earth.iloc[keep].drop(columns=FEATURES).copy()
        table.insert(0, "target", target["name"])
        table.insert(1, "body", target["body"])
        table.insert(2, "rank", base_rank[keep])
        table["score"] = base_score[keep]
        table["top_share"] = times_in_top[keep] / runs
        results.append(table)

    return pd.concat(results, ignore_index=True)


# ---------------------------------------------------------------------------
# 7. One final table: the best places for ALL targets together
# ---------------------------------------------------------------------------

def overall_ranking(results, good=0.5, exclude=()):
    """
    Join the tables of all targets into ONE ranking of Earth places.

    For every Earth place we average over the targets:
        mean_score      -> mean of 'score' (how good it is for all sites)
        sim_<feature>   -> mean similarity of each feature
        conditions_met  -> how many features have a mean similarity of at
                           least 'good' (0.5 by default), e.g. "4 of 6"
    Places that meet more conditions come first; ties are ordered by mean_score.
    'exclude' is a list of target names to leave out of the average.
    """
    results = results[~results["target"].isin(list(exclude))]
    sim_cols = [f"sim_{f}" for f in FEATURES if results[f"sim_{f}"].notna().any()]
    keys = [c for c in ("region", "place_hint", "lat", "lon") if c in results.columns]

    table = results.groupby(keys, sort=False)[["score"] + sim_cols].mean().reset_index()
    table = table.rename(columns={"score": "mean_score"}).dropna(subset=["mean_score"])
    met = (table[sim_cols] >= good).sum(axis=1)
    table["n_met"] = met
    table["conditions_met"] = met.astype(str) + f" of {len(sim_cols)}"
    table["weakest"] = table[sim_cols].idxmin(axis=1).str.replace("sim_", "")
    table = table.sort_values(["n_met", "mean_score"], ascending=False).reset_index(drop=True)
    table.insert(0, "rank", table.index + 1)
    return table


# ---------------------------------------------------------------------------
# 8. Command line
# ---------------------------------------------------------------------------

def print_by_target(table, columns, title, limit=None):
    """Print one small table per target."""
    with pd.option_context("display.width", 250, "display.max_columns", None,
                           "display.float_format", "{:.3f}".format):
        for name, group in table.groupby("target", sort=False):
            where = ""
            if "target_lat" in group.columns:
                where = f" at lat {group['target_lat'].iloc[0]:g}, lon {group['target_lon'].iloc[0]:g}"
            print(f"\n=== {name} ({group['body'].iloc[0]}{where}) - {title} ===")
            print(group[columns].head(limit).to_string(index=False, na_rep="-"))


def positive_int(text):
    """Used by argparse: accept only whole numbers bigger than 0."""
    value = int(text)
    if value < 1:
        raise argparse.ArgumentTypeError("must be 1 or bigger")
    return value


def main(argv=None):
    parser = argparse.ArgumentParser(description="Rank Earth cells as analogs of Moon/Mars sites.")
    parser.add_argument("--earth", default="data/earth_all.csv.gz", help="Earth cells CSV")
    parser.add_argument("--targets", default="data/targets.csv", help="Moon/Mars sites CSV")
    parser.add_argument("--top", type=positive_int, default=5,
                        help="How many analogs to print per target (default 5)")
    parser.add_argument("--out", help="Save the full results table to this CSV file")
    parser.add_argument("--weight", action="append", metavar="FEATURE=VALUE",
                        help="Change a weight, e.g. --weight precip_mm=0 (can repeat)")
    parser.add_argument("--sensitivity", type=positive_int, metavar="RUNS",
                        help="Also run the weight sensitivity check with this many runs (e.g. 200)")
    parser.add_argument("--spread", type=float, default=0.5,
                        help="How much the weights change in the sensitivity check (default 0.5 = +-50%%)")
    parser.add_argument("--scaling", choices=["tolerance", "robust"], default="tolerance",
                        help="How features are put on one scale (default: tolerance, see TOLERANCE)")
    parser.add_argument("--include-known", action="store_true",
                        help="Also rank famous analog regions (known = yes). By default they are "
                             "left out, because the challenge asks for little-known places")
    parser.add_argument("--exclude", action="append", default=[], metavar="TARGET",
                        help="Leave this target out of the final overall table (can repeat)")
    parser.add_argument("--out-overall", help="Save the final overall table to this CSV file")
    parser.add_argument("--min-coverage", type=float, default=1.0,
                        help="Share of the weight an Earth cell must have data for (default 1.0 = all)")
    args = parser.parse_args(argv)

    try:
        weights = parse_weights(args.weight)
        earth, targets = load_inputs(args.earth, args.targets)
        if "known" in earth.columns and not args.include_known:
            n_known = int((earth["known"] == "yes").sum())
            earth = earth[earth["known"] != "yes"].reset_index(drop=True)
            print(f"Left out {n_known:,} places in famous analog regions (use --include-known to see them).")
        results = compare_all(earth, targets, weights, scaling=args.scaling,
                              min_coverage=args.min_coverage)

        # Show the place name too, if the Earth file has one.
        place = [c for c in ("region", "place_hint") if c in results.columns]
        columns = ["rank", "lat", "lon"] + place + ["score"]
        columns += [f"sim_{f}" for f in FEATURES] + ["worst_match"]
        print_by_target(results, columns, f"top {args.top} Earth analogs", args.top)

        if args.out:
            results.to_csv(args.out, index=False)
            print(f"\nFull results saved to {args.out}")

        # Final table: best Earth places for all targets together.
        overall = overall_ranking(results, exclude=args.exclude)
        used = [t for t in results["target"].unique() if t not in args.exclude]
        print(f"\n=== OVERALL - best Earth places for all {len(used)} targets together ===")
        print("(conditions_met = features with a mean similarity of 0.5 or more)")
        shown = [c for c in overall.columns if c not in ("n_met", "target")]
        with pd.option_context("display.width", 250, "display.max_columns", None,
                               "display.float_format", "{:.3f}".format):
            print(overall[shown].head(args.top).to_string(index=False, na_rep="-"))
        if args.out_overall:
            overall.drop(columns="n_met").to_csv(args.out_overall, index=False)
            print(f"\nOverall table saved to {args.out_overall}")

        if args.sensitivity:
            stability = weight_sensitivity(earth, targets, weights, top=args.top,
                                           runs=args.sensitivity, spread=args.spread,
                                           scaling=args.scaling, min_coverage=args.min_coverage)
            columns = ["rank", "lat", "lon"] + place + ["score", "top_share"]
            print_by_target(stability, columns,
                            f"share of {args.sensitivity} runs inside the top {args.top} "
                            f"(weights changed by +-{args.spread:.0%})")
    except (ValueError, OSError) as err:
        # Show a short message instead of a long Python traceback.
        print(f"ERROR: {err}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
