# Earth Analogs for Moon and Mars Base Sites

NASA Space Apps Challenge 2026: **"Identify Earth Locations that Analog the Permanent Moon Base Locations and Mars"**.

The goal is to find places on Earth that look like the places where we want to build bases on the Moon and Mars, so that these Earth places can be used to test equipment, habitats and procedures. The challenge text is in `docs/NASA Space Apps Challenge.pdf`.

### What the challenge expects
- **Looking similar is not enough.** We must show with data *why* a place is a good analog.
- **An analogy does not have to be total.** We explain where it is similar, how similar, and **where it stops working**.
- **Look beyond the well-known analogs** (Antarctica, Atacama, Iceland, Hawaii) and find less-studied places.
- **Think about processes, not only places:** sedimentation, dust storms, volcanism, erosion, ice dynamics.
- **Scale matters:** a crater, a valley or a volcanic field can be a better analog than a whole desert.
- **Connect to exploration:** how the analog helps to test instruments, prepare operations, find resources or reduce risks.
- **Accept the limits of Earth:** reduced gravity, lunar vacuum, the thin Martian atmosphere and radiation cannot be reproduced.

### Analysis dimensions
| Dimension | Example variables |
|---|---|
| Geology and materials | Mineralogy, rock type, regolith |
| Terrain | Elevation, slope, roughness, craters |
| Extreme environment | Temperature, illumination, thermal range |
| Water and resources | Ice, permafrost, hydration |
| Atmospheric processes | Dust, wind, wind erosion |
| Habitability | Extremophiles, biosignatures |
| Subsurface | Caves, lava tubes |
| Operations | Landing, mobility, navigation, construction |

Other data sources (PDS, LRO/Diviner, Earthdata, Copernicus, RADARSAT, JAXA, etc.) are listed in [RECURSOS.md](RECURSOS.md).

---

## 1. The result in short

- **Earth database:** 691,035 places (cells of 0.05° ≈ 5.5 km) in **727 regions** of the world's drylands, polar deserts and high plateaus (`data/earth_all.csv.gz`). 133 regions are famous analogs (Atacama, Devon Island, Dry Valleys, Iceland…); they are kept as **controls** and left out of the rankings.
- **Targets:** 22 Moon south pole sites and 9 Mars sites in `data/targets.csv`. Moon: the **9 regions NASA kept in October 2024 as Artemis III candidate landing regions** (Peak near Cabeus B, Haworth, Malapert Massif, Mons Mouton Plateau, Mons Mouton, Nobile Rim 1, Nobile Rim 2, de Gerlache Rim 2, Slater Plain), the **7 regions of the first 2022 list that were dropped** (Peak near Shackleton, Connecting Ridge, Connecting Ridge Extension, de Gerlache Rim 1, de Gerlache-Kocher Massif, Faustini Rim A, Amundsen Rim), and 6 crater-scale sites (Shackleton, de Gerlache, Haworth and Faustini rims, Mons Mouton summit, and the shadowed Shackleton floor as a contrast site). Why each site matters and where it comes from: `data/moon_sites_sources.csv` and section 1.1. Mars: 9 sites (the landing sites of Perseverance, Curiosity, InSight, Opportunity, Spirit, Viking 1 and 2, Phoenix, plus Arcadia Planitia, a candidate for human missions).
- **Every place is described by the same 9 numbers** (section 2), measured the same way on the three bodies.
- **Outputs:** for every Moon/Mars site its best Earth analogs in 5 different parts of the world, a top 100 for the Moon and a top 100 for Mars (`outputs/results/top200_analogos.csv/.json`), the best months for a field campaign, side by side relief maps and photos (`maps/`), and one JSON file for the web app (`web/public/data/analogos.json`).


### 1.1 Why the Moon sites are all near the south pole

NASA plans the first Artemis landings and the Artemis Base Camp at the lunar south pole: crater rims and peaks there get sunlight for most of the year (solar power, milder temperatures), and the permanently shadowed craters next to them hold water ice. China and Russia (ILRS, Chang'e-7/8) and ESA also target the south pole, around Shackleton. So the south pole is where permanent bases are planned, not a bias of this project.

- **Artemis regions** (each about 15 × 15 km). NASA names the regions ([2024 update](https://www.nasa.gov/news-release/nasa-provides-update-on-artemis-iii-moon-landing-regions/)) but publishes no table of coordinates. We take the 130 candidate landing sites inside the regions from Wueller et al. 2026 (JGR Planets, doi:10.1029/2025JE009434; data on [Zenodo](https://zenodo.org/records/17084058), CC-BY-4.0). Each region becomes a disk: centre = mean of its landing sites, radius = farthest landing site + 2 km (their exploration area). The centre latitudes agree within ~0.2° with the "centerpoint latitudes" NASA lists from Lunar QuickMap (NTRS 20250007692). `python src/artemis_regions.py` recomputes them.
- **Leibnitz Beta Plateau** (2022 list) is the old name of Mons Mouton, so it is the same place as Mons Mouton Plateau and is not repeated.
- Every feature is measured exactly like the other Moon sites (LOLA 80 m terrain at 200 m pixels, Diviner PRP temperature, LOLA albedo, rock type from `src/composition.py`). All regions are feldspathic highlands; Haworth and Faustini Rim A, closer to the South Pole–Aitken basin, get a slightly more pyroxene-rich rock value.
- Not added yet (need new downloads): a north pole site (Peary crater rim, LOLA/Diviner north files, ~0.9 GB) and lava tube skylights (Marius Hills, Mare Tranquillitatis pit), which need global LOLA and Diviner maps.

---

## 2. The vector: 9 variables per place

Every place (an Earth cell or a Moon/Mars site) becomes a vector of 9 numbers, called **features**. The column names are the same in every file.

| Feature | What it means | Unit | Earth source | Moon source | Mars source |
|---|---|---|---|---|---|
| `elev_m` | mean elevation | m | NASADEM / Copernicus DEM | LOLA (above the 1737.4 km sphere) | HRSC+MOLA (above the areoid) |
| `slope_deg` | mean terrain slope | degrees | NASADEM / Copernicus DEM | LOLA 80 m | HRSC+MOLA 200 m |
| `roughness` | std. dev. of elevation in a 3 × 3 window | m | same DEM | LOLA | HRSC+MOLA |
| `temp_mean_K` | yearly mean surface temperature (day and night) | K | MODIS MOD11C3 | Diviner | Mars Climate Database |
| `temp_range_K` | warmest moment of the year minus the yearly mean | K | MODIS MOD11C3 | Diviner | Mars Climate Database |
| `albedo` | share of sunlight the surface reflects | 0–1 | MODIS MCD43C3 (white-sky, shortwave) | LOLA normal albedo (1064 nm) | TES albedo |
| `precip_mm` | yearly precipitation | mm | GPM IMERG (60°S–60°N), MERRA-2 (poles) | 0 | 0 |
| `ndvi` | vegetation index (≈0 = no plants) | –1…1 | MODIS MOD13C2 | 0 | 0 |
| `em_contrast` | rock type from thermal emissivity (big = silica-rich, ≈0 = basalt) | — | ASTER GED | calibrated estimate | calibrated estimate |

Important details that make the comparison fair:
- **Same terrain ruler on every body.** Slope and roughness depend on pixel size, so every elevation map (Earth 30–90 m, Moon 80 m, Mars 200 m) is first brought to **200 m pixels** (`src/terrain_common.py`), the coarsest of the three.
- **Same temperature definition.** `temp_range_K` = warmest monthly daytime value minus the yearly mean on Earth, Diviner yearly max minus mean on the Moon, and hottest moment minus yearly mean on Mars.
- **Precipitation at the poles.** GPM IMERG gives 0 mm over ice above 60°, which would make Greenland look as dry as the Moon. Above 60° we use MERRA-2 instead.
- **Rock type on the Moon and Mars.** There is no ASTER outside Earth. `src/composition.py` converts each site's lithology into the value an Earth rock of the same composition would give to ASTER, using the Christiansen feature (CF) as a bridge: `em_contrast = 2.1639 − 0.2625 · CF`, fitted with two anchors from our own ASTER data (Iceland basalt and Rub' al Khali quartz sand) and checked on the Puna. Moon CF comes from Diviner highland values in the literature, Mars CF from TES surface types plus rover ground truth. Uncertainty is ±0.026–0.039, about the size of the tolerance, so this variable gets a **half weight**. Full method: [docs/COMPOSICION.md](docs/COMPOSICION.md).
- `water_frac` (share of water in the cell) is also in the Earth table; cells that are mostly water are removed. It is not compared.

---

## 3. How the comparison works (`src/compare.py`)

1. **Read and check the files.** Missing columns or text instead of numbers stop the script with a clear `ERROR:`. Values that look like a unit mistake (for example Celsius instead of Kelvin) only give a `WARNING:`.
2. **Rain on a log scale.** `precip_mm` becomes `log(1 + mm)`, because going from 2 mm to 50 mm (desert to not desert) matters much more than 2000 mm to 2050 mm.
3. **Same scale for every feature (tolerances).** Every difference is divided by a **tolerance**: the difference we call "a lot". A difference of exactly one tolerance gives that feature a similarity of exp(–1) = 0.37; half a tolerance gives 0.61. Because the ruler is physical, a score means the same for every target and every region.

   | Feature | Tolerance |
   |---|---|
   | `elev_m` | 1000 m |
   | `slope_deg` | 5° |
   | `roughness` | 5 m |
   | `temp_mean_K` | 30 K |
   | `temp_range_K` | 30 K |
   | `albedo` | 0.10 |
   | `precip_mm` | 1.0 in log scale (≈ 2.7 times more or less rain) |
   | `ndvi` | 0.10 |
   | `em_contrast` | 0.03 |

   The first version used **one `RobustScaler` (scikit-learn) fitted on Earth and targets together** (median and interquartile range). With 80,000 Earth cells and a few Moon sites the ruler was set almost only by Earth, Moon temperatures were "100 rulers away" and every score was ~0. It is still available with `--scaling robust`, but tolerance scaling is the default.
4. **Weighted distance.** For each target and each Earth cell: `distance = sqrt( Σ wᵢ · dᵢ² / Σ wᵢ )`, where `dᵢ` is the scaled difference of feature *i* and `wᵢ` its weight. Dividing by the sum of the weights keeps targets with fewer features comparable.

   | Weights | `elev_m` | `temp_mean_K` | `em_contrast` | all others |
   |---|---|---|---|---|
   | `compare.py` defaults (`DEFAULT_WEIGHTS`) | 0.5 | 1.5 | 1.0 | 1.0 |
   | **Used for all official results** (`make_results.py`, `WEIGHTS`) | **0** | 1.5 | **0.5** | 1.0 |

   Elevation is switched off in the official results because each body measures height from a different zero level. `em_contrast` gets 0.5 because the Moon/Mars values are estimates.
5. **Score.** `score = exp(–distance)`: 1 = identical, near 0 = very different.
6. **Explanation per variable.** For every feature `sim_<feature> = exp(–|dᵢ|)` (0–1), plus `best_match` (where the analogy is strongest) and `worst_match` (where it **breaks**). This is how we show *why* a place got its score and *where the analogy stops*.
7. **Missing data.** If a target has no value for a feature, that feature is not used for that target. An Earth cell must have data for **all** the features the target uses (`--min-coverage 1.0`); otherwise a cell could win only because its bad feature was skipped.
8. **Famous analogs left out.** Earth places in regions with `known = yes` in `data/regions_catalog.csv` are removed before ranking (the challenge asks for less-studied places). `--include-known` puts them back, for example to use them as controls.
9. **Overall ranking.** `overall_ranking()` averages over all sites of one body: `mean_score`, mean `sim_*`, and `conditions_met` = how many features have a mean similarity ≥ 0.5 (for example "5 of 8"). Places that meet more conditions come first. The shadowed Shackleton floor is left out of the Moon average (it is a contrast site, not a base site). With 21 Moon sites in the average, 16 of them Artemis regions, the Moon ranking mostly reflects the Artemis landing regions.
10. **Sensitivity check (optional).** `--sensitivity 200` repeats the ranking 200 times with every weight multiplied by a random factor between 0.5 and 1.5 (`--spread 0.5`) and reports `top_share`: the share of runs in which the place stays in the top N. 1.0 = robust analog, not a lucky choice of weights.
11. **Variety in the results.** The best 20 cells of a site are often all in the same desert. `make_results.py` therefore also keeps the best place of each region and picks **5 regions at least 800 km apart** for every site (`MIN_SEPARATION_KM`). The top 100 lists keep places **at least 300 km apart**.

---

## 4. Input files: what the code accepts

Both inputs are CSV files. **`.csv.gz` (gzip) is read directly**, which is how the big Earth table is stored. Lines starting with `#` are comments. Extra columns are allowed and are carried into the outputs.

**Earth file** (default `data/earth_all.csv.gz`)
- required: `lat`, `lon`, and the 9 feature columns (a missing feature column is treated as empty).
- optional: `region` (region name, used for the per-region tables), `place_hint` (a readable name), `known` (`yes`/`no`, famous analog), `water_frac`.

**Targets file** (default `data/targets.csv`)
- required: `name` (unique), `body` (`Moon` or `Mars`), and the 9 feature columns. Leave a cell empty when a feature does not apply.
- optional: `site_lat`, `site_lon` (where the site is on the Moon/Mars; copied to the outputs as `target_lat`, `target_lon`), `area`, `n_dem_pixels`, `n_temp_points`.
- `data/targets_moon.csv` and `data/targets_mars.csv` are the same rows split by body (written by the target builders). `data/targets.csv` is both joined.

**Region catalog** `data/regions_catalog.csv`: `name, west, south, east, north, dem (nasadem | cop90), known (yes | no), why`. Add a row and run `python src/build_database.py` to add a region.

> **The sample files are FAKE.** `data/sample_earth.csv` and `data/sample_targets.csv` contain invented numbers ("(fake)" in the names, a `SYNTHETIC` header) and only 7 features. They exist only for the tests and to try the code. Never use their results.

---

## 5. The pipeline, step by step

Always run from the project folder, with the environment active.

| # | Command | Reads | Writes |
|---|---|---|---|
| 1 | `python src/download_earth.py --region W S E N --download` | NASA Earthdata (login) | `data/raw/NASADEM_HGT`, `MOD11C3`, `MCD43C3`, `GPM_3IMERGM` |
| 1b | `python src/download_earth.py --dem cop90 --region W S E N --download` | Copernicus DEM on AWS (no login) | `data/raw/COP90/` |
| 2 | `python src/build_earth.py --dem cop90 --name NAME --region W S E N --out data/regions/NAME.csv` | `data/raw/` | one region file |
| 3 | `python src/build_database.py` | `data/regions_catalog.csv` | `data/regions/*.csv` (missing ones) and **`data/earth_all.csv.gz`** |
| 4 | `python src/build_moon_targets.py` | LOLA + Diviner (PDS, downloaded once to `data/raw/moon/`) | `data/targets_moon.csv` (22 sites; Artemis region centres from `src/artemis_regions.py`) |
| 5 | `python src/build_mars_targets.py` | HRSC+MOLA DEM (read over the internet), TES albedo, Mars Climate Database | `data/targets_mars.csv` |
| 6 | `python src/composition.py --write` | `data/earth_all.csv.gz` (ASTER anchors) | `em_contrast` in `data/targets*.csv`, `data/composition_targets.csv` |
| 7 | `python src/make_results.py` | `data/earth_all.csv.gz`, `data/targets.csv` | `outputs/results/results_*.csv`, `seasons_*.csv` (calls `src/seasons.py`) |
| 8 | `python src/make_top_analogos.py` | results of step 7 | `outputs/results/top200_analogos.csv` and `.json` |
| 9 | `python src/make_maps.py` then `python src/make_photos.py` | DEMs, Sentinel-2, CTX, LROC | `maps/*.png`, `maps/index.csv`, `maps/photo_sources.csv` |
| 10 | `python src/export_web.py` | targets, composition, results, maps, photos | `web/public/data/analogos.json` (format: [web/DATOS.md](web/DATOS.md)) |

Helpers and one-off tools:
- `src/compare.py`: the similarity index itself (section 3); also usable alone (section 7).
- `src/terrain_common.py`: 200 m resampling, slope and roughness, shared by all builders.
- `src/seasons.py`: month by month score (MOD11C3 day/night temperature + monthly rain) for the best place of each region, with daylight hours, to choose the best month for a field campaign.
- `src/screen_global.py`: fast worldwide screening on the 0.05° climate grids (temperature, albedo, rain, vegetation; no terrain) to find candidate areas → `outputs/discovery/`.
- `src/grid_search/`: the worldwide drylands grid search that grew the database from 43 to 727 regions (see its [README](src/grid_search/README.md)).
- `src/checks/compare_before_after.py`: rankings before and after adding rock composition → `outputs/composition/`.

### Outputs (`outputs/results/`)
| File | Content |
|---|---|
| `results_pairs_top20.csv` | **most complete**: for every site its 20 best little-known Earth cells, with Earth values, site values (`target_*`), score, `sim_*`, best/worst match |
| `results_per_target_top_regions.csv` | best cell of the 5 best regions (≥ 800 km apart) for every site; used by the maps and the web app |
| `results_moon_overall.csv`, `results_mars_overall.csv` | top 1000 places for all sites of that body together |
| `results_moon_new_per_region.csv`, `results_mars_new_per_region.csv` | best place of each region |
| `seasons_moon.csv`, `seasons_mars.csv` | month by month score for those places |
| `top200_analogos.csv` / `.json` | top 100 Moon + top 100 Mars places (one per region, ≥ 300 km apart), each with its best site and all variables |

---

## 6. Data sources

All data is free. Versions and years are the ones in `data/raw/`.

### Earth
| Dataset | Used for | Version / period | Link |
|---|---|---|---|
| NASADEM_HGT | elevation, slope, roughness of the first test region (`northern_andes`) | v001, 1 arc-second | https://lpdaac.usgs.gov/products/nasadem_hgtv001/ |
| Copernicus DEM GLO-90 | elevation, slope, roughness for the other 726 regions (whole Earth, also above 60°N) | 3 arc-seconds (90 m), AWS open data | https://registry.opendata.aws/copernicus-dem/ |
| MODIS MOD11C3 | land surface temperature (mean and range; monthly day/night for seasons) | v061, 12 months of 2023, 0.05° | https://lpdaac.usgs.gov/products/mod11c3v061/ |
| MODIS MCD43C3 | white-sky shortwave albedo | v061, 15th of each month of 2023, 0.05° | https://lpdaac.usgs.gov/products/mcd43c3v061/ |
| GPM IMERG monthly (GPM_3IMERGM) | precipitation 60°S–60°N | V07B, 12 months of 2023, 0.1° | https://disc.gsfc.nasa.gov/datasets/GPM_3IMERGM_07/summary |
| MERRA-2 tavgM_2d_flx_Nx (M2TMNXFLX) | precipitation above 60° | 5.12.4, 12 months of 2023, 0.5° × 0.625° | https://disc.gsfc.nasa.gov/datasets/M2TMNXFLX_5.12.4/summary |
| MODIS MOD13C2 | NDVI (vegetation) | v061, 4 months of 2023 (one per season), 0.05° | https://lpdaac.usgs.gov/products/mod13c2v061/ |
| ASTER GED AG5KMMOH | emissivity bands 10–14 → `em_contrast` | v041 (GED v4.1), 5 km | https://lpdaac.usgs.gov/products/ag5kmmohv041/ |
| Sentinel-2 L2A (ESA Copernicus) | true colour photos of Earth analogs (`maps/*_photo.png`) | 10 m, via Element 84 Earth Search STAC | https://earth-search.aws.element84.com/v1 |
| Natural Earth admin 0 countries | country names in the grid search | 1:50m | https://www.naturalearthdata.com/ |

The download script covers NASADEM, MOD11C3, MCD43C3, GPM IMERG and Copernicus. MOD13C2, MERRA-2 and ASTER GED were downloaded from the same Earthdata archives (LP DAAC / GES DISC) into `data/raw/MOD13C2`, `data/raw/MERRA2_FLX` and `data/raw/AG5KMMOH`.

### Moon
| Dataset | Used for | Link |
|---|---|---|
| LRO LOLA GDR polar `ldem_80s_80m` | elevation, slope, roughness (80 m) | https://pds-geosciences.wustl.edu/lro/lro-l-lola-3-rdr-v1/lrolol_1xxx/data/lola_gdr/polar/float_img/ |
| LRO LOLA `ldam_50s_1000m` | normal albedo at 1064 nm | same folder |
| LRO Diviner polar resource product (PRP) south | yearly mean and max temperature (~500 m) | https://pds-geosciences.wustl.edu/lro/urn-nasa-pds-lro_diviner_derived1/data_derived_prp/ |
| Diviner Christiansen feature (literature: Greenhagen et al. 2010) | rock type (`em_contrast`) | [docs/COMPOSICION.md](docs/COMPOSICION.md) |
| LROC WAC south pole mosaic (100 m) | grey image of each site (`maps/*_B_moon_photo.png`) | https://pds.lroc.asu.edu/data/LRO-L-LROC-5-RDR-V1.0/LROLRC_2001/DATA/BDR/WAC_GLOBAL/ |
| USGS Gazetteer of Planetary Nomenclature | crater-scale site centres and diameters | https://planetarynames.wr.usgs.gov/ |
| NASA Artemis III candidate landing regions (2022 list of 13, 2024 list of 9) | which Moon sites to use | https://www.nasa.gov/news-release/nasa-provides-update-on-artemis-iii-moon-landing-regions/ |
| Wueller et al. 2026, candidate landing sites in the Artemis regions (`LandingSites.shp`) | centre and size of each Artemis region | https://zenodo.org/records/17084058 (to `data/raw/moon/artemis_sites/`) |
| LROC NAC oblique image, Apollo 12/15/16/17 Hasselblad photos | surface photos in the web app | https://www.lroc.asu.edu/ and https://images.nasa.gov/ |

### Mars
| Dataset | Used for | Link |
|---|---|---|
| HRSC + MOLA blended DEM, 200 m, v2 (USGS) | elevation, slope, roughness, relief maps (read over the internet, the file is 11 GB) | https://planetarymaps.usgs.gov/mosaic/Mars/HRSC_MOLA_Blend/ |
| MGS TES albedo mosaic, 7.4 km (USGS) | albedo | https://planetarymaps.usgs.gov/mosaic/Mars_MGS_TES_Albedo_mosaic_global_7410m.tif |
| Mars Climate Database v6.2 (LMD) | surface temperature for every season and hour | https://www-mars.lmd.jussieu.fr/ |
| TES surface types (Bandfield et al. 2000) + rover results; THEMIS/TES olivine at Nili Fossae (literature only) | rock type (`em_contrast`) | [docs/COMPOSICION.md](docs/COMPOSICION.md) |
| CTX global mosaic, 5 m (NASA/JPL/MSSS, Caltech Murray Lab), via Esri OnMars tiles | grey image of each site (`maps/*_B_mars_photo.png`) | https://murray-lab.caltech.edu/CTX/ |
| Rover photos from NASA Photojournal: Perseverance Mastcam-Z, Curiosity Mastcam, Opportunity and Spirit Pancam, Pathfinder IMP | surface photos in the web app (`experiments/fotos_analogos/`) | https://science.nasa.gov/photojournal/ |
| Mars 2020 / MSL waypoints (MMGIS) | exact coordinates of the rover photos | https://mars.nasa.gov/maps/ |

Credits and licences of every photo are in `experiments/fotos_analogos/imagenes/fotos.csv`, `experiments/fotos_analogos/sites.csv` and `maps/photo_sources.csv`, and are copied into the web JSON. HiRISE images are **not** used.

---

## 7. Limits of the analogy (be honest with the judges)

- **Earth cannot reproduce** reduced gravity, the lunar vacuum, the thin CO₂ atmosphere of Mars, cosmic and solar radiation, or the lunar day/night cycle (two weeks each). No Earth place is cold enough for the Moon: Moon scores are low (below 0.1) and `temp_mean_K` is often the `worst_match`. Moon analogs are "the least different places", useful for terrain, rock and operations, not for thermal tests.
- **Mars sites have no rain** but every Earth place has some; even the driest deserts lose some similarity in `precip_mm`.
- **Rock type on the Moon/Mars is an estimate** (±0.03), so it has half weight. It is a "rock-type equivalent", not what ASTER would measure there (regolith, dust and space weathering change the spectra).
- **Elevation is switched off**: heights on each body use a different reference.
- **One year of climate (2023)** and yearly means; `seasons.py` helps to choose the month.
- **Results reflect where we looked**: 727 regions of drylands, polar deserts and plateaus. China, Russia, the Middle East and Afghanistan were not included in the grid search.
- The **sample CSV files are fake** (section 4).

---

## 8. Folder structure

```
NASA_SPACE_APPS_2026/
├── README.md              <- this file
├── RECURSOS.md            <- catalog of possible data sources
├── CONTRIBUTING.md        <- git flow workflow (read before working)
├── environment.yml        <- conda environment "analogos"
├── .github/workflows/     <- automatic deploy of web/ to Azure Static Web Apps
├── docs/
│   ├── NASA Space Apps Challenge.pdf   <- the challenge description
│   ├── COMPOSICION.md     <- how rock type (em_contrast) is calibrated for Moon and Mars
│   ├── OBJETIVO.md        <- detailed goal of the platform and challenge criteria
│   ├── ARQUITECTURA.md    <- components, CI/CD, security and costs
│   ├── BITACORA.md        <- log of decisions and progress
│   └── GOOGLE_MAPS_API_KEY.md
├── data/                  <- INPUTS (see data/README.md)
│   ├── earth_all.csv.gz   <- the Earth database (727 regions, 691k places)
│   ├── regions/           <- one CSV per region (grid regions are not in git)
│   ├── regions_catalog.csv
│   ├── targets.csv, targets_moon.csv, targets_mars.csv
│   ├── composition_targets.csv
│   ├── sample_earth.csv, sample_targets.csv   <- FAKE, only for tests
│   └── raw/               <- downloaded files (not in git, ~9 GB)
├── src/                   <- all the code (section 5)
│   ├── grid_search/       <- worldwide grid search scripts
│   └── checks/            <- before/after comparisons
├── outputs/               <- RESULTS (see outputs/README.md)
│   ├── results/           <- rankings, seasons, top 200
│   ├── discovery/         <- global screening candidates
│   ├── composition/       <- effect of rock composition on the rankings
│   └── grid_search/       <- tiles selected by the grid search
├── maps/                  <- relief maps and photos, Earth analog next to its Moon/Mars site
├── experiments/fotos_analogos/  <- surface photos of the Moon/Mars sites with credits
├── tests/test_compare.py  <- automatic checks for compare.py
├── notebooks/             <- Jupyter notebooks
├── web/                   <- web platform (React + Vite + MapLibre + NASA GIBS)
└── infra/                 <- Azure infrastructure with Terraform (Free plans only)
```

---

## 9. Web platform (`web/`)

An interactive map to filter Earth analogs by target (Moon or Mars), type of environment (desert, polar, volcanic, crater, caves, salt flat) and similarity dimension. The map is a 3D globe with NASA imagery (GIBS): Blue Marble, recent satellite images, relief and land surface temperature. Each site can be opened in Google Earth.

You need Node.js and npm:

```fish
cd web
npm install
npm run dev                  # http://localhost:5173
```

Deployment to Azure is explained in [infra/README.md](infra/README.md).

The analysis results for the app (sites, Earth analogs, rock composition, images) are in
`web/public/data/analogos.json`, made with `python src/export_web.py` after `python src/make_results.py`.
`npm run dev` / `npm run build` first copy the images listed in the JSON into `web/public/data/img/` (`web/scripts/copy-data-images.mjs`).
Format and usage: [web/DATOS.md](web/DATOS.md). Rock composition method: [docs/COMPOSICION.md](docs/COMPOSICION.md).

---

## 10. Install the environment

All commands below work in the **fish** shell (and also in bash).

### 10.1 Install Miniconda (only once)

If you do not have `conda` yet, install Miniconda from https://docs.conda.io/en/latest/miniconda.html.

Fish needs one extra step so that `conda activate` works:

```fish
conda init fish
```

Then close the terminal and open a new one.

### 10.2 Create the `analogos` environment

From the project folder:

```fish
cd ~/NASA_SPACE_APPS_2026
conda env create -f environment.yml
conda activate analogos
```

This installs Python 3.12 with numpy, pandas, scikit-learn, xarray, rasterio, geopandas, matplotlib, folium and jupyter.

> Note: `environment.yml` has a `prefix:` line at the end with a path from one computer (`/home/marcop/miniconda3/envs/analogos`). On another computer you can delete that line; conda will then use its normal folder.

### 10.3 Extra packages

Only `compare.py` and the tests run with the base environment. The builders and map scripts also need packages that are not in `environment.yml` yet:

```fish
conda activate analogos
conda install -c conda-forge earthaccess pyhdf h5py pyproj scipy pillow requests shapely pyshp
```

| Package | Needed by |
|---|---|
| earthaccess | `download_earth.py` |
| pyhdf, h5py | `build_earth.py`, `seasons.py`, `screen_global.py` through `build_earth.py` (MODIS `.hdf`, IMERG/ASTER `.h5`, MERRA-2 `.nc4`) |
| pyproj, scipy | `build_moon_targets.py`, `terrain_common.py`, `make_maps.py`, `make_photos.py` |
| pillow, requests | `make_photos.py`, `experiments/fotos_analogos/build_images.py` |
| shapely, pyshp | `make_photos.py`, `src/grid_search/tiles.py` |

### 10.4 Update the environment later

```fish
conda env update -f environment.yml --prune
```

---

## 11. Run the similarity index alone (`src/compare.py`)

With no options it compares the real database with the real targets:

```fish
python src/compare.py --top 5
```

Try it with the fake sample data:

```fish
python src/compare.py --earth data/sample_earth.csv --targets data/sample_targets.csv --top 5
```

| Option | Default | What it does |
|---|---|---|
| `--earth FILE` | `data/earth_all.csv.gz` | Earth cells (CSV or CSV.GZ) |
| `--targets FILE` | `data/targets.csv` | Moon/Mars sites |
| `--top N` | `5` | how many analogs to print per target |
| `--out FILE` | (none) | save the **full** results table |
| `--out-overall FILE` | (none) | save the overall table (all targets together) |
| `--weight FEATURE=VALUE` | (none) | change one weight, e.g. `--weight elev_m=0`. Can repeat. |
| `--scaling tolerance\|robust` | `tolerance` | how features are put on one scale (section 3) |
| `--include-known` | off | also rank famous analog regions |
| `--exclude TARGET` | (none) | leave a target out of the overall table. Can repeat. |
| `--min-coverage X` | `1.0` | share of the weight a cell must have data for |
| `--sensitivity RUNS` | off | weight sensitivity check, e.g. `200` |
| `--spread X` | `0.5` | how much weights change in the sensitivity check (±50%) |

To get the same numbers as the official results:

```fish
python src/compare.py --weight elev_m=0 --weight em_contrast=0.5 --exclude "Shackleton floor (shadow)"
```

Settings at the top of `src/compare.py`: `FEATURES`, `DEFAULT_WEIGHTS`, `BODY_WEIGHTS`, `LOG_FEATURES`, `TOLERANCE`, `VALID_RANGES`.

---

## 12. Run the tests

```fish
python tests/test_compare.py
```

You should see `ok` for each test and then `All 13 tests passed.` The tests use invented numbers and check the maths (a cell identical to the target gets score 1, weight 0 switches a feature off, empty values do not break anything, the worst match names the broken feature…). They also work with `pytest tests/`.

---

## 13. Download the NASA Earth data (`src/download_earth.py`)

### 13.1 Before the first download (only once)

1. Create a **free NASA Earthdata Login** account: https://urs.earthdata.nasa.gov/users/new
2. For **GPM** and **MERRA-2** you must also approve one application: go to https://urs.earthdata.nasa.gov/profile, open **Authorized Apps**, click **Approve More Applications**, and approve **NASA GESDISC DATA ARCHIVE**.
3. Optional: save your login so you are not asked every time (writes `~/.netrc`):

   ```fish
   python -c "import earthaccess; earthaccess.login(persist=True)"
   ```

### 13.2 See the plan, then download

```fish
python src/download_earth.py --region -80 -5 -66 13              # plan only, no login
python src/download_earth.py --region -80 -5 -66 13 --download   # really download
python src/download_earth.py --dem cop90 --region -10 20 0 30 --download   # Copernicus tiles only
```

The region is **WEST SOUTH EAST NORTH** in degrees. It only controls the elevation tiles; the other datasets are global files.

| Option | Default | What it does |
|---|---|---|
| `--region WEST SOUTH EAST NORTH` | (required) | area for the elevation tiles |
| `--year YEAR` | `2023` | year for the monthly data |
| `--dem nasadem\|cop90` | `nasadem` | `nasadem`: NASADEM + MOD11C3 + MCD43C3 + GPM. `cop90`: only Copernicus DEM tiles (no login) |
| `--download` | off | really download; without it you only see the plan |

Files go to `data/raw/<dataset>/` (ignored by git). Files that already exist are skipped. Size guide: 12 MCD43C3 files ≈ 2.4 GB, 12 MOD11C3 files ≈ 0.9 GB, a NASADEM tile 5–20 MB.

---

## 14. Documentation

- [docs/COMPOSICION.md](docs/COMPOSICION.md): rock type (`em_contrast`) for the Moon and Mars
- [data/README.md](data/README.md): every input file
- [outputs/README.md](outputs/README.md): every result file
- [src/grid_search/README.md](src/grid_search/README.md): the worldwide grid search
- [web/DATOS.md](web/DATOS.md): the JSON for the web app
- [docs/OBJETIVO.md](docs/OBJETIVO.md): detailed goal of the platform and challenge criteria
- [docs/ARQUITECTURA.md](docs/ARQUITECTURA.md): components, CI/CD, security and costs
- [docs/BITACORA.md](docs/BITACORA.md): log of decisions and progress
- [docs/GOOGLE_MAPS_API_KEY.md](docs/GOOGLE_MAPS_API_KEY.md): how to create and test a Google Maps API key
- [RECURSOS.md](RECURSOS.md): data sources

## 15. How to collaborate

We use **git flow**. Read [CONTRIBUTING.md](CONTRIBUTING.md) before you start working.
