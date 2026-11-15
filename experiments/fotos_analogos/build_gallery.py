"""
Write sites.csv and galeria.html from the site metadata below,
images_info.json (made by build_images.py) and analogs.csv (build_analogs.py).

Run from the repo root:
    python experiments/fotos_analogos/build_gallery.py
"""
import html
import json
import os

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
PD_NASA = "Public domain (NASA/JPL image use policy; credit requested)"
LROC_LIC = "NASA mission image, free to use with credit NASA/GSFC/Arizona State University"

SITES = [
    dict(id="01", target_name="Jezero crater (Perseverance)", body="Mars",
         image_title="Mastcam-Z's First 360-Degree Panorama", pia_or_product_id="PIA24264",
         mission_instrument="Mars 2020 Perseverance / Mastcam-Z", sol_or_date="Sol 3 (2021-02-21)",
         credit="NASA/JPL-Caltech/MSSS/ASU", licence=PD_NASA,
         source_page="https://science.nasa.gov/photojournal/mastcam-zs-first-360-degree-panorama/",
         download_url="https://assets.science.nasa.gov/content/dam/science/psd/photojournal/pia/pia24/pia24264/PIA24264.tif",
         note="Surface 360° panorama. Copied from experiments/panorama_360/pia (not re-downloaded). "
              "The 640 MB PIA24264_hires.tif (36952x11570) exceeds 60 MB."),
    dict(id="02", target_name="Gale crater (Curiosity)", body="Mars",
         image_title="Mount Sharp Panorama in White-Balanced Colors", pia_or_product_id="PIA16768",
         mission_instrument="MSL Curiosity / Mastcam (100 mm)", sol_or_date="Released 2013-03-15",
         credit="NASA/JPL-Caltech/MSSS", licence=PD_NASA,
         source_page="https://photojournal.jpl.nasa.gov/catalog/PIA16768",
         download_url="https://assets.science.nasa.gov/content/dam/science/psd/photojournal/pia/pia16/pia16768/PIA16768.jpg",
         note="Surface mosaic. White-balanced: the sky looks too blue, terrain as under Earth light. "
              "TIFF is 84 MB (> 60 MB) so the full-size JPEG was used."),
    dict(id="03", target_name="Vastitas Borealis (Phoenix)", body="Mars",
         image_title="Looking out Across the Martian Polar Plains", pia_or_product_id="PIA10693",
         mission_instrument="Phoenix Mars Lander / SSI (Surface Stereo Imager)",
         sol_or_date="Sol 0 (landing 2008-05-25)",
         credit="NASA/JPL-Caltech/University of Arizona/Texas A&M", licence=PD_NASA,
         source_page="https://photojournal.jpl.nasa.gov/catalog/PIA10693",
         download_url="https://assets.science.nasa.gov/content/dam/science/psd/photojournal/pia/pia10/pia10693/PIA10693.tif",
         note="Surface view, approximate colour, but LOW RESOLUTION: only 640x360 (still of an animation; "
              "JPEG is 21 KB, TIFF 0.7 MB). Preview is not upscaled. A larger Phoenix panorama would be better."),
    dict(id="04", target_name="Shackleton rim", body="Moon",
         image_title="On the Rim! (oblique view of the rim of Shackleton crater)",
         pia_or_product_id="NAC M1224655261LR (NASA page labels it M1195011983LR)",
         mission_instrument="LRO / LROC NAC", sol_or_date="",
         credit="NASA/GSFC/Arizona State University", licence=LROC_LIC,
         source_page="https://www.lroc.asu.edu/posts/993",
         download_url="https://lroc.im-ldi.com/ptif/zoomify/02_Shack_M1224655261_LRmos.2016aug_20180112_110035/ (Zoomify tiles, full level)",
         note="Orbital oblique view, not surface. Full 3750x3750 rebuilt from LROC Zoomify tiles "
              "(NASA image-detail copy is only 952x952). Most of the frame is black: crater interior in permanent shadow."),
    dict(id="05", target_name="de Gerlache rim", body="Moon",
         image_title="Traversing the Shackleton de Gerlache Ridge", pia_or_product_id="NAC M1348682369LR",
         mission_instrument="LRO / LROC NAC", sol_or_date="",
         credit="NASA/GSFC/Arizona State University", licence=LROC_LIC,
         source_page="https://www.lroc.asu.edu/images/1247",
         download_url="https://lroc.im-ldi.com/ckeditor_assets/pictures/1130/original_M1348682369_LRmos.warp.str01.shrunk6x.1100x1100.png",
         note="Orbital oblique view, not surface. Ridge ~14 km long; Shackleton rim on the left. "
              "1100x1100 is the largest version published (LROC original = NASA copy; no zoomable full-res)."),
    dict(id="06", target_name="Mons Mouton summit", body="Moon",
         image_title="IM-2 Athena Seen Obliquely", pia_or_product_id="NAC M1495922531LR",
         mission_instrument="LRO / LROC NAC", sol_or_date="2025-03-07 16:54:21 UTC",
         credit="NASA/GSFC/Arizona State University", licence=LROC_LIC,
         source_page="https://www.lroc.asu.edu/images/1408",
         download_url="https://lroc.im-ldi.com/ptif/zoomify/M1495922531_LRmos.warp.str01_str02.4zoom_20250308_134300/ (Zoomify tiles, 1/2 res level)",
         note="Orbital oblique view, not surface: Intuitive Machines IM-2 Athena landing site near the centre of "
              "Mons Mouton (84.79°S, 29.20°E), ~23.5 h after touchdown. LROC (NASA) image, not an IM photo. "
              "Full NAC mosaic is 31000x10000; rebuilt at half resolution from Zoomify tiles to stay < 60 MB."),
]

LABELS = {"elev_m": "elevación", "slope_deg": "pendiente", "roughness": "rugosidad",
          "temp_mean_K": "temperatura media", "temp_range_K": "rango térmico", "albedo": "albedo",
          "precip_mm": "precipitación", "ndvi": "vegetación (NDVI)", "em_contrast": "contraste EM",
          "water_frac": "agua"}


def main():
    targets = pd.read_csv("data/targets.csv").set_index("name")
    info = json.load(open(os.path.join(HERE, "images_info.json")))
    rows = []
    for s in SITES:
        t = targets.loc[s["target_name"]]
        i = info[s["id"]]
        rows.append({**{k: s[k] for k in ("id", "target_name", "body")},
                     "site_lat": t.site_lat, "site_lon": t.site_lon,
                     **{k: s[k] for k in ("image_title", "pia_or_product_id", "mission_instrument",
                                          "sol_or_date", "credit", "licence", "source_page", "download_url")},
                     "file": i["file"], "preview": i["file"].replace("images/", "images/previews/").rsplit(".", 1)[0] + ".jpg",
                     "width": i["width"], "height": i["height"], "size_mb": i["size_mb"], "note": s["note"]})
    sites = pd.DataFrame(rows)
    sites.to_csv(os.path.join(HERE, "sites.csv"), index=False)

    analogs = pd.read_csv(os.path.join(HERE, "analogs.csv")).fillna("")
    e = html.escape
    cards = []
    for s, meta in zip(sites.itertuples(), SITES):
        a = analogs[analogs.target == s.target_name]
        items = []
        for r in a.itertuples():
            photo = r.earth_photo or r.earth_photo_same_cell_other_target
            img = ""
            if photo:
                cap = "" if r.earth_photo else " (foto hecha para otro objetivo, misma celda)"
                img = (f'<a href="../../{e(photo)}"><img class="earth" loading="lazy" src="../../{e(photo)}" '
                       f'alt="Foto de {e(r.region)}"></a><small>{cap}</small>')
            tag = "Nuevo" if r.set == "new" else "Análogo conocido"
            gm = f"https://www.google.com/maps/@{r.lat},{r.lon},10z"
            items.append(f"""
        <li class="{r.set}">
          <div class="row"><span class="tag">{tag} #{r.rank}</span>
            <b>{e(r.region.replace('_', ' '))}</b>
            <span class="score">score {r.score:.3f}</span></div>
          <div class="sub">{r.lat:.3f}, {r.lon:.3f} · <a href="{gm}" target="_blank" rel="noopener">Google Maps</a>
            · mejor: {LABELS.get(r.best_match, r.best_match)} · peor: {LABELS.get(r.worst_match, r.worst_match)}</div>
          {img}
        </li>""")
        view = "Vista desde la superficie" if s.body == "Mars" else "Vista orbital oblicua (LRO), no de superficie"
        lowres = " lowres" if s.width < 1000 else ""
        cards.append(f"""
    <article class="card">
      <a href="{e(s.file)}"><img class="site{lowres}" loading="lazy" src="{e(s.preview)}" alt="{e(s.image_title)}"></a>
      <div class="body">
        <p class="kicker">{'Marte' if s.body == 'Mars' else 'Luna'} · {e(view)}</p>
        <h2>{e(s.target_name)}</h2>
        <p class="meta">{s.site_lat:.2f}°, {s.site_lon:.2f}° · {e(s.image_title)} ({e(s.pia_or_product_id)})<br>
          {e(s.mission_instrument)}{' · ' + e(s.sol_or_date) if s.sol_or_date else ''}<br>
          Crédito: {e(s.credit)} · {s.width}×{s.height} px, {s.size_mb} MB ·
          <a href="{e(s.source_page)}" target="_blank" rel="noopener">fuente</a></p>
        <p class="note">{e(meta['note'])}</p>
        <h3>Análogos terrestres</h3>
        <ul>{''.join(items)}
        </ul>
      </div>
    </article>""")

    page = f"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Galería de análogos</title>
<style>
:root {{ --bg:#f6f5f2; --card:#fff; --ink:#1d1d1f; --muted:#5f6368; --line:#e3e1dc; --accent:#b4441c; --known:#2b6cb0; }}
@media (prefers-color-scheme: dark) {{ :root {{ --bg:#141414; --card:#1f1f1f; --ink:#ececec; --muted:#a0a0a0; --line:#333; --accent:#f08a5d; --known:#7fb2ef; }} }}
* {{ box-sizing:border-box; }}
body {{ margin:0; background:var(--bg); color:var(--ink); font:15px/1.5 system-ui, sans-serif; }}
header {{ max-width:1100px; margin:auto; padding:32px 16px 8px; }}
h1 {{ margin:0 0 6px; font-size:28px; }}
header p {{ color:var(--muted); margin:0; }}
main {{ max-width:1100px; margin:auto; padding:16px; display:grid; gap:24px; }}
.card {{ background:var(--card); border:1px solid var(--line); border-radius:12px; overflow:hidden; }}
img.site {{ width:100%; max-height:520px; object-fit:contain; background:#000; display:block; }}
img.site.lowres {{ image-rendering:auto; max-height:360px; }}
.body {{ padding:16px 20px 20px; }}
.kicker {{ margin:0; color:var(--accent); font-weight:600; font-size:13px; text-transform:uppercase; letter-spacing:.04em; }}
h2 {{ margin:4px 0 6px; }}
h3 {{ margin:16px 0 6px; font-size:16px; }}
.meta, .sub, small {{ color:var(--muted); font-size:13px; }}
.note {{ font-size:13px; border-left:3px solid var(--line); padding-left:10px; }}
ul {{ list-style:none; padding:0; margin:0; display:grid; gap:10px; }}
li {{ border-top:1px solid var(--line); padding-top:8px; }}
.row {{ display:flex; gap:10px; align-items:baseline; flex-wrap:wrap; }}
.tag {{ font-size:12px; font-weight:600; color:var(--accent); }}
li.known .tag {{ color:var(--known); }}
.score {{ margin-left:auto; font-variant-numeric:tabular-nums; }}
img.earth {{ margin-top:6px; width:100%; max-width:520px; border-radius:6px; display:block; }}
a {{ color:inherit; }}
</style>
</head>
<body>
<header>
  <h1>Galería de análogos Luna / Marte – Tierra</h1>
  <p>Una imagen de alta resolución por sitio (NASA) y sus 3 mejores regiones análogas en la Tierra
  según <code>src/compare.py</code> (peso de elevación = 0), más el mejor análogo ya conocido.
  Las imágenes de la Luna son vistas orbitales oblicuas del LRO: no existen fotos de superficie en el polo sur.</p>
</header>
<main>{''.join(cards)}
</main>
</body>
</html>
"""
    with open(os.path.join(HERE, "galeria.html"), "w", encoding="utf-8") as f:
        f.write(page)
    print("wrote sites.csv and galeria.html")


if __name__ == "__main__":
    main()
