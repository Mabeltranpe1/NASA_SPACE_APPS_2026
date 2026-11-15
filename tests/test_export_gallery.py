"""Offline tests for the curated gallery (data/gallery_sources.json) and src/export_gallery.py."""

import json
import re
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import export_gallery as eg  # noqa: E402

SOURCES = json.loads((ROOT / "data/gallery_sources.json").read_text(encoding="utf-8"))
KINDS = {"rover", "lander", "apollo", "orbital", "visualization", "field", "astronaut", "satellite", "radar"}


def test_every_entry_is_complete():
    for place, entries in SOURCES["places"].items():
        assert entries, place
        for e in entries:
            assert e["kind"] in KINDS, (place, e)
            assert e.get("es") and e.get("en"), (place, e)
            assert ("nasa_id" in e) != ("svs" in e and "file" in e), (place, e)


def test_every_moon_and_mars_target_has_photos():
    sites_ts = (ROOT / "web/src/data/sites.ts").read_text(encoding="utf-8")
    homologues = set(re.findall(r"\{ id: '([\w-]+)', body: '(?:luna|marte)'", sites_ts))
    data = json.loads((ROOT / "web/public/data/comparisons.json").read_text(encoding="utf-8"))
    targets = {t["id"] for t in data["targets"]}
    covered = set(SOURCES["places"]) | set(SOURCES["aliases"])
    assert not (homologues | targets) - covered, sorted((homologues | targets) - covered)


def test_trim_removes_black_borders_but_keeps_dark_terrain():
    img = Image.new("RGB", (400, 300), (0, 0, 0))
    img.paste((40, 40, 40), (50, 20, 350, 280))  # dark (lunar-like) content
    out = eg.trim_and_fit(img)
    assert out.size == (300, 260)


def test_extreme_panoramas_are_cropped():
    out = eg.trim_and_fit(Image.new("RGB", (5000, 500), (120, 90, 60)))
    assert abs(out.width / out.height - eg.MAX_ASPECT) < 0.01
    assert max(out.size) <= eg.MAX_SIDE


def test_credit_is_read_from_the_description():
    assert eg.nasa_credit("A view of Gale. Image credit: NASA/JPL-Caltech/MSSS", "JPL") == "NASA/JPL-Caltech/MSSS"
    assert eg.nasa_credit("No credit line here", "ARC") == "NASA/ARC"
    assert eg.nasa_credit("Text", "JPL", "NASA/JPL-Caltech/ASU/MSSS") == "NASA/JPL-Caltech/ASU/MSSS"
