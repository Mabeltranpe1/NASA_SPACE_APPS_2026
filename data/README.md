# What each file in data/ is

## The database (inputs)
- `earth_all.csv` – ALL Earth places (one row = one 0.05° cell, ~5.5 km), with the 9 variables. Column `known` = yes for famous analogs (controls). **Main Earth file.**
- `regions/<name>.csv` – the same, one file per region. `earth_all.csv` is made from these.
- `regions_catalog.csv` – list of regions (box, elevation source, known yes/no, why). Add a row and run `python src/build_database.py`.
- `targets.csv` – all Moon and Mars sites together. **Main target file.**
- `targets_moon.csv`, `targets_mars.csv` – the same, split by body (built by `build_moon_targets.py` / `build_mars_targets.py`).
- `raw/` – downloaded NASA files (not in git).

## Results (outputs, can be made again at any time)
- `discovery_mars_new.csv`, `discovery_moon_new.csv` – NEW candidate areas from the global screening (famous zones left out). `discovery_mars.csv` / `discovery_moon.csv` = full list including famous zones.
- `results_mars_new_per_region.csv`, `results_moon_new_per_region.csv` – best little-known place in each region.
- `results_mars_overall.csv`, `results_moon_overall.csv` – top 1000 little-known places for all sites of that body together.
- `results_pairs_top20.csv` – **most complete result**: for every Moon/Mars site, its 20 best little-known Earth places. Each row has the Earth place (lat, lon and all its values), the Moon/Mars site (target_lat, target_lon and all its values as target_*), the score and the similarity of each variable.
- `seasons_mars.csv`, `seasons_moon.csv` – month by month score for the best place of each region.

## Other
- `sample_earth.csv`, `sample_targets.csv` – FAKE example data, only to try the code.
- `archive/` – old files from earlier tests, no longer used. Safe to delete.
