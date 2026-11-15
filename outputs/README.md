# What each folder in outputs/ is

`outputs/` holds **results**: everything here can be made again from `data/` with the scripts in `src/`. Famous analog regions (`known = yes`) are always left out. Method: main [README](../README.md), section 3.

## results/ (made by `python src/make_results.py` and `python src/make_top_analogos.py`)
Official weights: `elev_m` 0, `em_contrast` 0.5, the rest as in `compare.py`.
- `results_pairs_top20.csv` – **most complete result**: for every Moon/Mars site, its 20 best little-known Earth cells. Each row has the Earth place (`region, lat, lon` and its values), the site (`target_lat, target_lon` and `target_*` values), `score`, `sim_*` per variable, `best_match` and `worst_match`.
- `results_per_target_top_regions.csv` – for every site, the best cell of its 5 best regions, at least 800 km apart (`region_rank` 1–5). Used by `make_maps.py` and `export_web.py`.
- `results_moon_overall.csv`, `results_mars_overall.csv` – top 1000 places for all sites of that body together (`mean_score`, mean `sim_*`, `conditions_met` = variables with mean similarity ≥ 0.5, `weakest`). The shadowed Shackleton floor is left out of the Moon average.
- `results_moon_new_per_region.csv`, `results_mars_new_per_region.csv` – best place of each region from the overall table.
- `seasons_moon.csv`, `seasons_mars.csv` – month by month score (temperature and dryness) and daylight hours for those places (`src/seasons.py`).
- `top200_analogos.csv`, `top200_analogos.json` – top 100 places for the Moon and 100 for Mars, one per region and at least 300 km apart, each with its best site, its score for every site and all the variables of both places.

## discovery/ (made by `python src/screen_global.py`)
Fast worldwide screening on the 0.05° climate grids (temperature, albedo, rain, vegetation; no terrain), used to choose where to build new regions.
- `discovery_moon.csv`, `discovery_mars.csv` – best 10 × 10° areas, including famous zones, with a ready `box_west_south_east_north`.
- `discovery_moon_new.csv`, `discovery_mars_new.csv` – only new candidate areas (famous and avoided zones left out).

## composition/ (made by `python src/checks/compare_before_after.py`)
How the rankings changed when rock type (`em_contrast`) was added for the Moon and Mars: `overall_*_before.csv` (no composition), `overall_*_after.csv` (weight 1.0), `overall_*_after_w05.csv` (weight 0.5, the one we use), `per_target_before_after.csv`, `regions_*_before_after.csv`. `backup_results_before/` keeps the official results from before the change. See [docs/COMPOSICION.md](../docs/COMPOSICION.md).

## grid_search/
- `selected_tiles.csv` – the 1 × 1° Copernicus tiles chosen by the worldwide grid search, and why (`src/grid_search/select.py`). See [src/grid_search/README.md](../src/grid_search/README.md).
