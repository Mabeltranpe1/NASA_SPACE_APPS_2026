> Documentación técnica del comparador escrita por Marco (originalmente el README de la rama `feature/compare_analysis`). Se movió aquí al integrar su trabajo; el README principal del proyecto sigue en la raíz. Las rutas relativas se escribieron pensando en la raíz del repositorio.
>
> **Versión histórica (14 de noviembre).** Algunas partes ya no valen: la escala por defecto es la de tolerancias físicas (`TOLERANCE`), no `RobustScaler`; la base tiene 727 regiones y 31 sitios; hay 13 tests. La versión al día es [DATOS_Y_METODO.md](DATOS_Y_METODO.md), y la API, [API.md](API.md).

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

Other data sources (PDS, LRO/Diviner, Earthdata, Copernicus, RADARSAT, JAXA, etc.) are listed in [RECURSOS.md](../RECURSOS.md).


---

## 1. How it works (the idea)

We describe every place (an Earth grid cell or a Moon/Mars site) with the same 7 numbers, called **features**:

| Feature | What it means | Unit |
|---|---|---|
| `elev_m` | elevation | metres |
| `slope_deg` | terrain slope | degrees |
| `roughness` | how rough the terrain is | no unit |
| `temp_mean_K` | mean surface temperature | Kelvin |
| `temp_range_K` | day-night / seasonal temperature range | Kelvin |
| `albedo` | how much sunlight the surface reflects | 0 to 1 |
| `precip_mm` | yearly precipitation | mm |

Then `src/compare.py` does this:

1. **Same scale for everybody.** Elevation is in thousands of metres and albedo is between 0 and 1, so we must rescale them. We use **one** `RobustScaler` (from scikit-learn) fitted on Earth and targets **together**, so Earth, Moon and Mars are measured with the same ruler. `precip_mm` is first changed with `log(1 + x)`, because the step from 2 mm to 50 mm (desert to not desert) matters much more than 2000 mm to 2050 mm.
2. **Distance.** For each target and each Earth cell we compute a **weighted Euclidean distance**. Weights say how important each feature is (default: `temp_mean_K` = 1.5, `elev_m` = 0.5, the rest = 1.0). A weight of 0 switches a feature off.
3. **Score.** The distance becomes a score between 0 and 1 with `score = exp(-distance)`. 1 means identical, near 0 means very different.
4. **Explanation.** For every feature we also give a similarity `sim_<feature>` (0 to 1), plus `best_match` (where the analogy is strongest) and `worst_match` (where the analogy **breaks**). So you can see **why** a place got its score.
5. **Sensitivity check (optional).** We repeat the ranking many times with randomly changed weights (default +-50%) and count how often each Earth cell stays in the top N (`top_share`). A value of 1.0 means the place is a robust analog, not just a lucky result of one choice of weights.

Missing data is handled like this:
- If a **target** has an empty value (for example no rain on the Moon), that feature is not used for that target.
- If an **Earth cell** has an empty value, that feature is not used for that cell only.

---

## 2. Data sources (NASA Earthdata, all free)

| Dataset | Gives us | Resolution | Downloaded part |
|---|---|---|---|
| **NASADEM_HGT** v001 | elevation, later slope and roughness | 30 m tiles (1 x 1 degree) | only the tiles inside your region |
| **MOD11C3** v061 | land surface temperature, monthly | 0.05 degree, global | 12 files (one per month) |
| **MCD43C3** v061 | surface albedo (daily product) | 0.05 degree, global | 12 files (the 15th of each month) |
| **GPM_3IMERGM** v07 | precipitation, monthly | 0.1 degree, global | 12 files (one per month) |

The Moon and Mars target values are not downloaded by a script yet (see "Status and next steps"). More data sources are listed in [RECURSOS.md](../RECURSOS.md).

---

## 3. Folder structure

```
NASA_SPACE_APPS_2026/
├── README.md              <- main README (Spanish): how to use the app, the API and the setup
├── RECURSOS.md            <- catalog of data sources
├── CONTRIBUTING.md        <- git flow workflow (read before working)
├── environment.yml        <- conda environment "analogos"
├── .gitignore             <- ignores data/raw/, *.hdf, *.tif, *.nc, __pycache__/ ...
├── .github/workflows/     <- automatic deploy to Azure Static Web Apps
├── docs/
│   ├── NASA Space Apps Challenge.pdf   <- the challenge description
│   ├── OBJETIVO.md        <- detailed goal of the platform and challenge criteria
│   ├── ARQUITECTURA.md    <- components, CI/CD, security and costs
│   ├── BITACORA.md        <- log of decisions and progress
│   └── GOOGLE_MAPS_API_KEY.md  <- how to create and test a Google Maps API key
├── data/
│   ├── sample_earth.csv   <- FAKE Earth cells, only for testing
│   ├── sample_targets.csv <- FAKE Moon/Mars sites, only for testing
│   ├── raw/               <- downloaded NASA files (not in git, can be many GB)
│   │   ├── NASADEM_HGT/
│   │   ├── MOD11C3/
│   │   ├── MCD43C3/
│   │   └── GPM_3IMERGM/
│   └── processed/         <- processed data (not in git)
├── notebooks/             <- Jupyter notebooks for exploration and analysis
├── src/
│   ├── compare.py         <- the similarity index (main script)
│   └── download_earth.py  <- downloads the NASA Earth data
├── tests/
│   └── test_compare.py    <- automatic checks for compare.py
├── outputs/               <- maps, figures and final results
├── web/                   <- web platform (React + Vite + MapLibre + NASA GIBS)
└── infra/                 <- Azure infrastructure with Terraform (Free plans only)
```

> **Important: the sample CSV files are FAKE.** `data/sample_earth.csv` and `data/sample_targets.csv` contain invented numbers. They exist only to test that `compare.py` works. The place names have "(fake)" in them, and the script prints a `SYNTHETIC sample data` warning when you use them. Do not use their results in the final presentation.

---

## 4. Web platform (`web/`)

An interactive map to filter Earth analogs by target (Moon or Mars), type of environment (desert, polar, volcanic, crater, caves, salt flat) and similarity dimension. The map is a 3D globe with NASA imagery (GIBS): Blue Marble, recent satellite images, relief and land surface temperature. Each site can be opened in Google Earth.

You need Node.js and npm:

```fish
cd web
npm install
npm run dev                  # http://localhost:5173
```

Deployment to Azure is explained in [infra/README.md](../infra/README.md).

---

## 5. Install the environment

All commands below work in the **fish** shell (and also in bash).

### 5.1 Install Miniconda (only once)

If you do not have `conda` yet, install Miniconda from https://docs.conda.io/en/latest/miniconda.html.

Fish needs one extra step so that `conda activate` works:

```fish
conda init fish
```

Then close the terminal and open a new one.

### 5.2 Create the `analogos` environment

From the project folder:

```fish
cd ~/NASA_SPACE_APPS_2026
conda env create -f environment.yml
conda activate analogos
```

This installs Python 3.12 with numpy, pandas, scikit-learn, xarray, rasterio, geopandas, matplotlib, folium and jupyter.

> Note: `environment.yml` has a `prefix:` line at the end with a path from one computer (`/home/marcop/miniconda3/envs/analogos`). On another computer you can delete that line; conda will then use its normal folder.

### 5.3 Extra packages for downloading and reading NASA files

`download_earth.py` needs **earthaccess**, which is not in `environment.yml` yet. To read the NASA files later you will probably also need **pyhdf** (for the `.hdf` files of MOD11C3 and MCD43C3) and **h5py** (for the GPM files). Install them with:

```fish
conda activate analogos
conda install -c conda-forge earthaccess pyhdf h5py
```

If conda cannot solve it, you can try `pip install earthaccess h5py` instead (pyhdf is easier to install with conda).

### 5.4 Check that it works

```fish
python -c "import numpy, pandas, sklearn, earthaccess; print('OK')"
```

### 5.5 Update the environment later

If someone adds a package to `environment.yml`:

```fish
conda env update -f environment.yml --prune
```

---

## 6. Run the similarity index (`src/compare.py`)

Always run the commands **from the project folder** (the paths are relative to it), with the environment active.

### 6.1 Try it with the fake sample data

```fish
python src/compare.py --earth data/sample_earth.csv --targets data/sample_targets.csv --top 5
```

For each target you get a small table: rank, lat, lon, place_hint, score, the `sim_*` columns and `worst_match`.

> If you run `python src/compare.py` with no `--earth` / `--targets`, it looks for `data/earth.csv` and `data/targets.csv`. These files do **not** exist yet, so for now always give the sample files.

### 6.2 All options

| Option | Default | What it does |
|---|---|---|
| `--earth FILE` | `data/earth.csv` | CSV with the Earth cells |
| `--targets FILE` | `data/targets.csv` | CSV with the Moon/Mars sites |
| `--top N` | `5` | how many analogs to print per target |
| `--out FILE` | (none) | save the **full** results table to a CSV file |
| `--weight FEATURE=VALUE` | (none) | change one weight, e.g. `--weight precip_mm=0`. You can repeat it. |
| `--sensitivity RUNS` | (off) | also run the weight sensitivity check, e.g. `200` runs |
| `--spread X` | `0.5` | how much weights change in the sensitivity check (0.5 = +-50%) |

### 6.3 Examples

Switch elevation off and save everything to a file:

```fish
python src/compare.py --earth data/sample_earth.csv --targets data/sample_targets.csv --weight elev_m=0 --out results.csv
```

Check if the ranking is stable when the weights change:

```fish
python src/compare.py --earth data/sample_earth.csv --targets data/sample_targets.csv --sensitivity 200
```

Change two weights at the same time:

```fish
python src/compare.py --earth data/sample_earth.csv --targets data/sample_targets.csv --weight temp_mean_K=3 --weight albedo=0.5
```

### 6.4 Input file format

Both files are CSV. Lines that start with `#` are comments.

- **Earth file:** columns `lat`, `lon`, plus the 7 feature columns. An optional `place_hint` column (a name) is shown in the output.
- **Targets file:** columns `name`, `body` (`Moon` or `Mars`), plus the 7 feature columns. Names must be unique. Leave a cell empty when a body does not have that feature (for example `precip_mm` on the Moon and Mars).

The script stops with a clear `ERROR:` if a column is missing or contains text instead of numbers. It prints a `WARNING:` (but continues) if values look like a unit mistake, for example a temperature in Celsius instead of Kelvin.

### 6.5 Settings inside the code

At the top of `src/compare.py` you can edit:
- `FEATURES` (which columns are compared),
- `DEFAULT_WEIGHTS`,
- `BODY_WEIGHTS` (different weights for Moon or Mars only, e.g. `{"Moon": {"precip_mm": 0.0}}`),
- `LOG_FEATURES`,
- `VALID_RANGES` (limits used for the unit warnings).

---

## 7. Run the tests

```fish
python tests/test_compare.py
```

You should see `ok` for each test and then `All 10 tests passed.` The tests use invented numbers and only check that the maths behaves correctly (for example: a cell identical to the target gets score 1, weight 0 switches a feature off, empty values do not break anything).

They also work with pytest, if you install it (`conda install pytest`, then `pytest tests/`).

---

## 8. Download the NASA Earth data (`src/download_earth.py`)

### 8.1 Before the first download (only once)

1. Create a **free NASA Earthdata Login** account: https://urs.earthdata.nasa.gov/users/new
2. For **GPM** (precipitation) you must also approve one application: go to https://urs.earthdata.nasa.gov/profile, open **Authorized Apps**, click **Approve More Applications**, and approve **NASA GESDISC DATA ARCHIVE**. Without this, the GPM download is skipped (the script tells you).
3. Optional: save your login so you are not asked every time. This writes it to `~/.netrc`:

   ```fish
   python -c "import earthaccess; earthaccess.login(persist=True)"
   ```

### 8.2 Step 1: see the plan (no login needed)

```fish
python src/download_earth.py --region -80 -5 -66 13
```

The region is **WEST SOUTH EAST NORTH** in degrees (longitude, latitude, longitude, latitude). West and south are negative numbers. The region only controls the elevation tiles (NASADEM); the other three datasets are global files.

This shows how many files and how many GB each dataset needs, and how much free disk space you have. Nothing is downloaded.

### 8.3 Step 2: really download

```fish
python src/download_earth.py --region -80 -5 -66 13 --download
```

Options:

| Option | Default | What it does |
|---|---|---|
| `--region WEST SOUTH EAST NORTH` | (required) | area for the elevation tiles |
| `--year YEAR` | `2023` | year for the monthly data (2001 to last year) |
| `--download` | (off) | really download; without it you only see the plan |

Files go to `data/raw/<dataset>/`. Git ignores this folder. Files that already exist are skipped, so you can stop the script and run it again at any time. If one dataset fails, the others continue; just run the script again later.

Size guide: the 12 MCD43C3 albedo files are about 2.4 GB and the 12 MOD11C3 files about 0.9 GB. The NASADEM tiles are about 5-20 MB each.

---

## 9. Status and next steps

**Done**
- `src/compare.py`: similarity index, per-feature explanation, weight sensitivity check.
- `tests/test_compare.py`: 10 tests, all passing.
- `src/download_earth.py`: downloads the four Earth datasets.
- Data for 2023 already in `data/raw/`: NASADEM tiles for the region about 81°W-66°W, 6°S-13°N, 12 MOD11C3 files and 12 MCD43C3 files.

**Not done yet**
- `data/raw/GPM_3IMERGM/` is still empty: approve "NASA GESDISC DATA ARCHIVE" (section 8.1) and run the download again.
- Add `earthaccess` (and `pyhdf`, `h5py` if used) to `environment.yml`.
- Write a script that turns the raw files into `data/earth.csv`: unzip and mosaic the NASADEM tiles, compute slope and roughness, compute mean and range of temperature, mean albedo and yearly precipitation, all on one common grid.
- Build `data/targets.csv` with **real** Moon and Mars values for the base candidate sites (for example from LRO/LOLA, Diviner for the Moon and MOLA, THEMIS, TES for Mars).
- Make maps of the results (folium / matplotlib are already installed).

---

## 10. Documentation

- [docs/OBJETIVO.md](OBJETIVO.md): detailed goal of the platform and challenge criteria
- [docs/ARQUITECTURA.md](ARQUITECTURA.md): components, CI/CD, security and costs
- [docs/BITACORA.md](BITACORA.md): log of decisions and progress
- [docs/GOOGLE_MAPS_API_KEY.md](GOOGLE_MAPS_API_KEY.md): how to create and test a Google Maps API key
- [RECURSOS.md](../RECURSOS.md): data sources

## 11. How to collaborate

We use **git flow**. Read [CONTRIBUTING.md](../CONTRIBUTING.md) before you start working.
