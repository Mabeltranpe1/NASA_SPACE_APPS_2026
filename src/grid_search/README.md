# Worldwide grid search (`src/grid_search/`)

On 2026-11-15 these scripts grew the Earth database from 43 hand-picked regions (~164k places) to **727 regions (~691k places)**, because the first results only reflected where we had looked, not the whole planet.

They are a **record of a one-off run** (made on a large cloud machine), kept so the method can be checked and repeated. They are not part of the normal pipeline: to add regions today, add rows to `data/regions_catalog.csv` and run `python src/build_database.py`.

## Order and what each script does

| # | Script | Reads | Writes (in `outputs/grid_search/`) |
|---|---|---|---|
| 1 | `screen_cells.py` | global 0.05° grids in `data/raw/` (temperature, albedo, rain, vegetation) via `src/screen_global.py`, `data/targets.csv` | `cells.parquet`: Moon and Mars screening score of every land cell |
| 2 | `tiles.py` | `cells.parquet`, Natural Earth countries (`ne/ne_50m_admin_0_countries`), `data/regions_catalog.csv` | `tiles.csv`: one row per 1 × 1° tile with rain, NDVI, albedo, temperature, best 10% scores, country, and whether a region already covers it |
| 3 | `select.py` | `tiles.csv` | `selected_tiles.csv` (in git): the tiles to build and why |
| 4 | `build_grid.py` | `selected_tiles.csv`, Copernicus tiles in `data/raw/COP90/` | `data/regions/<country>_<lat>n_<lon>e.csv` (one per 2 × 2° area) and `grid_catalog_rows.csv` (rows added to `data/regions_catalog.csv`) |

After step 4, `python src/build_database.py` joins everything into `data/earth_all.csv.gz`, and `python src/make_results.py` remakes the results.

## Tile selection rules (`select.py`)
- **Arid land checkerboard:** tiles with rain < 300 mm/year and NDVI < 0.25, one of every two tiles.
- **Best screening tiles:** the 400 best Mars tiles and the 250 best Moon tiles, inside semi-arid land (rain < 500 mm, NDVI < 0.35).
- **Named zones** added by hand: Richat, Patagonia, Tierra del Fuego, Peru/Bolivia Andes, Ustyurt, Kyzylkum, Karakum (Darvaza), Betpak-Dala, southern Puna.
- **Skipped:** China, Russia, the Middle East and Afghanistan (team decision), Antarctica, tiles already covered by a region, and very bright tiles (albedo ≥ 0.55, ice and snow).
- Areas near famous analogs got `known = yes` in the catalog, so they are controls and are left out of the rankings.

## Needed only for this run
- Intermediate files `cells.parquet`, `tiles.csv`, `grid_catalog_rows.csv` and the Natural Earth shapefile go in `outputs/grid_search/` (not in git).
- Packages: `shapely`, `pyshp` (and `pyarrow` for parquet).
