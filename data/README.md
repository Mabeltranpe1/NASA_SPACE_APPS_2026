# What each file in data/ is

`data/` holds the **inputs** of the comparison. Everything the code produces from them is in `outputs/` (see [outputs/README.md](../outputs/README.md)). How the files are used: main [README](../README.md), sections 4 and 5.

## The Earth database
- `earth_all.csv.gz` – **main Earth file.** All Earth places in one gzip CSV (pandas and `compare.py` read it directly): 691,035 cells of 0.05° (~5.5 km) from 727 regions. Columns: `region, lat, lon`, the 9 features (`elev_m, slope_deg, roughness, temp_mean_K, temp_range_K, albedo, precip_mm, ndvi, em_contrast`), `water_frac` and `known` (`yes` = famous analog, kept only as a control). Made by `python src/build_database.py`. Never commit an uncompressed `earth_all.csv` (it is in `.gitignore`).
- `regions/<name>.csv` – the same columns, one file per region. `earth_all.csv.gz` is made from these. Only the 43 hand-picked regions are in git; the 684 grid search regions (`<country>_<lat>n_<lon>e.csv`, 2 × 2° areas) are ignored by git and can be rebuilt with `src/build_database.py`.
- `regions_catalog.csv` – one row per region: `name, west, south, east, north, dem (nasadem | cop90), known (yes | no), why`. Add a row and run `python src/build_database.py` to add a region.

## The Moon and Mars sites
- `targets.csv` – **main target file.** All 6 Moon and 9 Mars sites: `name, body, site_lat, site_lon, area`, the 9 features, `n_dem_pixels, n_temp_points`.
- `targets_moon.csv`, `targets_mars.csv` – the same rows split by body, written by `src/build_moon_targets.py` / `src/build_mars_targets.py`.
- `composition_targets.csv` – rock type of every site: lithology, Christiansen feature (CF) and its uncertainty, `em_contrast` and its uncertainty, and the evidence (papers, missions). Written by `python src/composition.py --write`; method in [docs/COMPOSICION.md](../docs/COMPOSICION.md).

## Other
- `sample_earth.csv`, `sample_targets.csv` – **FAKE** example data with only 7 features, used by `tests/test_compare.py` and to try the code. Never use their results.
- `raw/` – downloaded files, not in git (~9 GB): `NASADEM_HGT/`, `COP90/`, `MOD11C3/`, `MCD43C3/`, `MOD13C2/`, `GPM_3IMERGM/`, `MERRA2_FLX/`, `AG5KMMOH/`, `moon/` (LOLA, Diviner), `mars/` (TES albedo, Mars Climate Database). Sources and versions: main README, section 6.
- `processed/` – free space for processed data (not in git).
