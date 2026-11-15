"""Offline tests for src/export_images.py (no network)."""

import math
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import export_images as ei  # noqa: E402


def test_crop_box_keeps_the_ground_square():
    for lat in (0.0, 45.0, 75.38, 82.22, -77.5):
        west, south, east, north = ei.crop_box(lat, 10.0)
        assert math.isclose(north - south, 2 * ei.HALF_LAT_DEG)
        # East-west ground distance equals the north-south one.
        ew_km = (east - west) * 111.32 * math.cos(math.radians(lat))
        assert math.isclose(ew_km, (north - south) * 111.32, rel_tol=1e-6)


def test_crop_box_is_centered():
    west, south, east, north = ei.crop_box(3.23, -75.17)
    assert math.isclose((west + east) / 2, -75.17)
    assert math.isclose((south + north) / 2, 3.23)


def test_empty_share_detects_black_borders():
    assert ei.empty_share(Image.new("RGB", (64, 64), (0, 0, 0))) == 1.0
    assert ei.empty_share(Image.new("RGB", (64, 64), (120, 100, 80))) == 0.0
    half = Image.new("RGB", (64, 64), (120, 100, 80))
    half.paste((0, 0, 0), (0, 0, 32, 64))
    assert math.isclose(ei.empty_share(half), 0.5, abs_tol=0.02)


def test_places_include_catalog_and_discoveries_once():
    places = ei.places(ROOT / "web/src/data/sites.ts", ROOT / "web/public/data/comparisons.json")
    ids = [p["id"] for p in places]
    assert len(ids) == len(set(ids))
    assert "tatacoa" in ids and "lava-beds" in ids  # catalog, even without data
    assert any(i.startswith("cell_") for i in ids)  # discoveries
