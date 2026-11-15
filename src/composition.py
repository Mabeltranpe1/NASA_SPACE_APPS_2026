"""
composition.py - Rock-type value (em_contrast) for Moon and Mars sites,
calibrated so it can be compared with the ASTER value used on Earth.

THE PROBLEM
    On Earth, em_contrast comes from ASTER GED (build_earth.py):
        em_contrast = mean emissivity of bands 13-14 (10.6-11.3 um)
                    - mean emissivity of bands 10-12 (8.3-9.1 um)
    Silica-rich rock (quartz sand, granite) -> big value; basalt -> about 0.
    There is no ASTER on the Moon or Mars, and the instruments there measure
    other things:
        Moon : LRO Diviner has 3 narrow channels at 7.8 / 8.25 / 8.55 um. It
               measures the position of the Christiansen feature (CF), NOT the
               8-11 um bands that ASTER uses.
        Mars : MGS TES measures full spectra, and the global result is a
               small set of "surface types" (Bandfield et al. 2000):
               Surface Type 1 = basalt, Surface Type 2 = basaltic andesite /
               weathered basalt, plus dust-covered areas.

THE BRIDGE: the Christiansen feature position (CF, in micrometres)
    CF is an emissivity maximum just before the silicate bands. It moves to
    shorter wavelengths when a rock has more silica (more polymerised
    silicates) and to longer wavelengths with more olivine/pyroxene.
    Typical laboratory values (Salisbury & Walter 1989; Cooper et al. 2002;
    Greenhagen et al. 2010):
        quartz ~7.3-7.4 | granite ~7.8-7.9 | andesite ~8.0-8.1
        anorthosite (plagioclase) ~7.9-8.1 | basalt ~8.2-8.3 | olivine ~8.6+
    The SAME silica trend moves the ASTER bands: that is why em_contrast is
    big for quartz and ~0 for basalt.

    Step 1 (Earth, measured): we fit a straight line em_contrast = a + b * CF
        with two anchors taken from OUR OWN ASTER database, so the value is on
        exactly the same scale as the Earth cells:
            basalt     : median of Iceland highlands     (CF 8.25 um)
            quartz sand: median of Rub' al Khali dunes   (CF 7.45 um)
        Check: an andesitic/dacitic volcanic region (Puna, CF ~8.05) must fall
        near the line. It is printed by `python src/composition.py`.
    Step 2 (Moon/Mars, from the literature): every site gets a CF value:
        Moon: Diviner CF of the feldspathic highlands (the polar sites are
              outside the global Diviner CF maps, which need warm daytime
              surfaces, so the regional highland value is used).
        Mars: the TES surface type + rover ground truth -> lithology -> CF.
    Step 3: em_contrast = a + b * CF, with an uncertainty from the CF range.

WHAT THIS VALUE IS (AND IS NOT)
    It is a "rock-type equivalent": the em_contrast an Earth rock of the same
    composition would show to ASTER. It is NOT what ASTER would measure on the
    Moon or Mars: fine regolith and dust in vacuum/low pressure have much
    weaker spectral bands, and lunar space weathering and the lunar thermal
    environment shift the CF by ~0.1 um (in opposite directions; here they
    are assumed to cancel). See docs/COMPOSICION.md.

Example:
    python src/composition.py              # show the calibration
    python src/composition.py --write      # put the values in the targets CSVs
"""

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
EARTH = ROOT / "data" / "earth_all.csv"
TARGET_FILES = [ROOT / "data" / f for f in ("targets.csv", "targets_moon.csv", "targets_mars.csv")]
SITE_TABLE = ROOT / "data" / "composition_targets.csv"

# Earth anchors: (region in earth_all.csv, lithology, laboratory CF in um)
ANCHORS = {
    "basalt": ("iceland_highlands", "fresh basaltic lava and tephra", 8.25),
    "quartz_sand": ("rub_al_khali", "quartz-dominated dune sand", 7.45),
}
# Independent check (not used in the fit)
CHECKS = [("puna", "andesitic-dacitic volcanics", 8.05)]

# Every Moon/Mars site: (lithology, CF in um, CF uncertainty in um, evidence)
SITES = {
    # --- Moon: south polar feldspathic highlands -------------------------
    "Shackleton rim": ("feldspathic highland (anorthositic)", 8.15, 0.10,
                       "Diviner highland CF ~8.1-8.2 um (Greenhagen 2010); Shackleton on SPA rim, "
                       "plagioclase-rich (Kaguya)"),
    "de Gerlache rim": ("feldspathic highland (anorthositic)", 8.15, 0.10,
                        "Diviner highland CF ~8.1-8.2 um; same terrain as Shackleton"),
    "Haworth rim": ("feldspathic highland, some noritic SPA ejecta", 8.18, 0.10,
                    "Diviner highland CF; closer to SPA basin (more pyroxene)"),
    "Faustini rim": ("feldspathic highland, some noritic SPA ejecta", 8.18, 0.10,
                     "Diviner highland CF; closer to SPA basin (more pyroxene)"),
    "Mons Mouton summit": ("feldspathic massif (SPA rim)", 8.15, 0.10,
                           "Diviner highland CF; SPA rim massif"),
    "Shackleton floor (shadow)": ("feldspathic highland (cold trap)", 8.15, 0.15,
                                  "No CF in permanent shadow (no sunlight); same rock as the rim, "
                                  "larger uncertainty (possible frost)"),
    # --- Mars --------------------------------------------------------------
    "Jezero crater (Perseverance)": ("olivine-rich basalt + carbonates", 8.40, 0.10,
                                     "TES/THEMIS olivine-rich Nili Fossae region; Perseverance: "
                                     "Seitah olivine cumulate, Maaz basalt"),
    "Gale crater (Curiosity)": ("basalt (olivine-bearing sand, mudstones)", 8.30, 0.10,
                                "TES Surface Type 1 nearby; Bagnold dunes olivine basalt (Curiosity)"),
    "Elysium Planitia (InSight)": ("basaltic lava under dust", 8.25, 0.15,
                                   "Dust-covered in TES (high dust cover index); basaltic plains"),
    "Meridiani Planum (Opportunity)": ("basaltic sand + hematite", 8.25, 0.10,
                                       "TES Surface Type 1 + hematite (Christensen 2000); Opportunity"),
    "Gusev crater (Spirit)": ("olivine basalt", 8.35, 0.12,
                              "Spirit: Adirondack-class olivine basalt; moderately dusty"),
    "Chryse Planitia (Viking 1)": ("basaltic plains under dust", 8.25, 0.15,
                                   "Moderately dusty in TES; basaltic soils (Viking)"),
    "Utopia Planitia (Viking 2)": ("Surface Type 2 (andesite-like / weathered basalt)", 8.10, 0.12,
                                   "TES Surface Type 2 dominates the northern lowlands (Bandfield 2000; "
                                   "Wyatt & McSween 2002)"),
    "Vastitas Borealis (Phoenix)": ("Surface Type 2 (andesite-like / weathered basalt)", 8.10, 0.12,
                                    "TES Surface Type 2 northern plains"),
    "Arcadia Planitia (human candidate)": ("Surface Type 2 under some dust", 8.15, 0.15,
                                           "Northern lowlands (Type 2) with moderate dust"),
}


def calibration(earth=None):
    """Fit em_contrast = a + b * CF with the two Earth anchors. Returns (a, b, info)."""
    if earth is None:
        earth = pd.read_csv(EARTH, usecols=["region", "em_contrast"])
    info = {}
    for key, (region, lith, cf) in ANCHORS.items():
        values = earth.loc[earth["region"] == region, "em_contrast"].dropna()
        if values.empty:
            raise ValueError(f"No ASTER values for anchor region '{region}' in {EARTH}")
        info[key] = dict(region=region, lithology=lith, cf=cf, median=values.median(),
                         p10=values.quantile(0.1), p90=values.quantile(0.9), n=len(values))
    (cf1, e1), (cf2, e2) = [(info[k]["cf"], info[k]["median"]) for k in ANCHORS]
    b = (e2 - e1) / (cf2 - cf1)
    a = e1 - b * cf1
    for region, lith, cf in CHECKS:
        values = earth.loc[earth["region"] == region, "em_contrast"].dropna()
        info[f"check_{region}"] = dict(region=region, lithology=lith, cf=cf,
                                       median=values.median() if len(values) else np.nan,
                                       predicted=a + b * cf)
    return a, b, info


def site_values(a, b):
    """One row per Moon/Mars site with CF, em_contrast and its uncertainty."""
    rows = []
    for name, (lith, cf, cf_sigma, evidence) in SITES.items():
        rows.append(dict(name=name, lithology=lith, cf_um=cf, cf_sigma_um=cf_sigma,
                         em_contrast=round(a + b * cf, 4),
                         em_contrast_sigma=round(abs(b) * cf_sigma, 4), evidence=evidence))
    return pd.DataFrame(rows)


def em_contrast_for(name):
    """Value for one site (used by build_moon/mars_targets.py). NaN if unknown or no Earth data."""
    if name not in SITES or not EARTH.exists():
        return np.nan
    a, b, _ = calibration()
    return round(a + b * SITES[name][1], 4)


def write_targets(values):
    """Fill em_contrast in the targets CSV files (other columns are not touched)."""
    lookup = values.set_index("name")["em_contrast"]
    for path in TARGET_FILES:
        if not path.exists():
            continue
        table = pd.read_csv(path)
        missing = sorted(set(table["name"]) - set(lookup.index))
        if missing:
            print(f"WARNING: {path.name}: no composition for {missing}", file=sys.stderr)
        table["em_contrast"] = table["name"].map(lookup)
        table.to_csv(path, index=False)
        print(f"  em_contrast written to {path.relative_to(ROOT)}")


def main():
    parser = argparse.ArgumentParser(description="Calibrate em_contrast for Moon and Mars sites.")
    parser.add_argument("--write", action="store_true",
                        help="Write the values into data/targets*.csv and data/composition_targets.csv")
    args = parser.parse_args()

    a, b, info = calibration()
    print("Earth anchors (ASTER GED, our own database):")
    for key in ANCHORS:
        i = info[key]
        print(f"  {key:12s} {i['region']:18s} CF {i['cf']:.2f} um  em_contrast median {i['median']:+.4f} "
              f"(P10 {i['p10']:+.4f}, P90 {i['p90']:+.4f}, n={i['n']})")
    print(f"\nLine: em_contrast = {a:+.4f} {b:+.4f} * CF   ({b:+.4f} per um of CF)")
    for region, _, _ in CHECKS:
        c = info[f"check_{region}"]
        print(f"Check {region} ({c['lithology']}, CF ~{c['cf']}): predicted {c['predicted']:+.4f}, "
              f"ASTER median {c['median']:+.4f}")

    values = site_values(a, b)
    with pd.option_context("display.width", 200, "display.max_colwidth", 45):
        print("\n" + values.drop(columns="evidence").to_string(index=False))

    if args.write:
        values.to_csv(SITE_TABLE, index=False)
        print(f"\n  site table written to {SITE_TABLE.relative_to(ROOT)}")
        write_targets(values)


if __name__ == "__main__":
    main()
