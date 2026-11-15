# What each file in data/ is

## The database (inputs)
- `earth_all.csv.gz` – **active expanded Earth database**, 691,035 cells and 727 regions. Each row is a 0.05° cell; east-west width varies with latitude. Nine compared variables plus geographic/provenance columns. `known=yes` marks reference controls.
- `earth_all.csv` – preserved older 163,998-cell / 43-region reference; not the integration's active input.
- `regions/<name>.csv` – available regional construction inputs. The clone does not contain every intermediate CSV used to build the expanded gzip. A partial merge is rejected before changing that published database.
- `regions_catalog.csv` – 727 region boxes, elevation sources, control flags and selection notes. Serving/exporting the existing app does not require downloading these regions again.
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
- `archive/` – historical references. `archive/integration-main/` preserves the pre-integration data and web exports that differ from the incoming global contribution. Keep these originals when reviewing the integration.
- `reference/marco_analogos.json` – original legacy web contract from Marco, preserved separately from the canonical v3 web data.
- `features/`, `results/`, `figures/`, the small 200 m DEMs and climate series – original regional science from Santiago; see `docs/SCIENTIFIC_DATA_CONTRACT.md`.
- `top200_analogos.csv` / `.json` – original 100 Moon + 100 Mars ranking, kept without changing its global scores or ordering.

## Unified publication

`python src/export_web.py` reads the expanded gzip and original regional products, computes web comparable-dimension scores, exports references to the complete original global ranking and publishes lazy regional scientific documents. It does not replace global cells with regional statistics or combine global scores with PAI. `python src/export_science.py` refreshes only regional scientific exports. Neither command downloads datasets.

## Maps (folder maps/ at the project root)
- One image per place. Same number = same Moon/Mars site. `B` = the Moon/Mars site, `A1`, `A2`, `A3` = its 3 best little-known Earth analogs (each from a different region). All images of one number show a square of the same size, at 200 m pixels. `maps/index.csv` lists every pair. Made by `python src/make_maps.py`.
