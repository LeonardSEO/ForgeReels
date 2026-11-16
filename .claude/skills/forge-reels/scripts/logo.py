#!/usr/bin/env python3
"""Fetch brand logos for a video that names real companies or products ("Instagram vs Facebook").

  ~/forge-reels/venv/bin/python -I logo.py --project reels/<video> Instagram Facebook "Hugging Face"

Per brand: <project>/art/logos/<slug>.svg (or .png), a sidecar <slug>.json (source, licence, brand colour) and a line
in <project>/licences.md. Prints the `logo` component to paste into scene.json.
Sources, in order: Simple Icons (CC0 icon files, one colour, the brand's own hex), then Wikimedia Commons (the first
SVG/PNG whose title names the brand and "logo"; its licence is recorded as found). A brand neither has: search the
web for the company's press / brand page, save the file by hand into art/logos/ and write the sidecar yourself.

Logos are trademarks whatever the file's licence says: use them only to NAME the company the video talks about,
never to suggest it made or endorses the video, and never redraw or recolour them.
"""
import argparse
import datetime
import json
import pathlib
import re
import sys
import urllib.parse
import urllib.request

UA = {"User-Agent": "ForgeReels/1.0 (logo fetcher)"}
SI = "https://cdn.jsdelivr.net/npm/simple-icons@latest"
SUBS = {"+": "plus", ".": "dot", "&": "and", "đ": "d", "ħ": "h", "ı": "i", "ĸ": "k", "ŀ": "l", "ł": "l", "ß": "ss", "ŧ": "t"}


def slugify(title):
    """Simple Icons' slug rule: lower case, a few symbols spelled out, everything else that is not a-z0-9 dropped."""
    s = title.lower()
    for a, b in SUBS.items():
        s = s.replace(a, b)
    return re.sub(r"[^a-z0-9]", "", s)


def pick(brand, icons):
    """The Simple Icons entry for a brand name (by title or slug, ignoring case and punctuation), or None."""
    want = slugify(brand)
    for i in icons:
        if want in (i.get("slug") or slugify(i["title"]), slugify(i["title"])):
            return i
    return None


def commons_choice(brand, pages):
    """The Commons SVG/PNG whose title is closest to "<brand> logo" (fewest other words; years do not count);
    (title, info) or None. "Microsoft logo (2012)" beats "Microsoft Office logos (2013-2019)"."""
    words = [w for w in re.split(r"\W+", brand.lower()) if w]
    best = None
    for p in sorted(pages, key=lambda v: v.get("index", 0)):
        ii = (p.get("imageinfo") or [{}])[0]
        t = [w for w in re.split(r"\W+", re.sub(r"^file:|\.\w+$", "", p.get("title", "").lower())) if w and not w.isdigit()]
        if "logo" not in t or not all(w in t for w in words) or ii.get("mime") not in ("image/svg+xml", "image/png"):
            continue
        extra = len([w for w in t if w not in words and w != "logo"])
        if best is None or extra < best[0]:
            best = (extra, p["title"], ii)
    return best and best[1:]


def get(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30).read()


def simple_icons(brand):
    raw = json.loads(get(SI + "/data/simple-icons.json"))
    icon = pick(brand, raw["icons"] if isinstance(raw, dict) else raw)
    if not icon:
        return None
    slug = icon.get("slug") or slugify(icon["title"])
    svg = get(f"{SI}/icons/{slug}.svg").decode("utf-8").replace("<svg ", f'<svg fill="#{icon["hex"]}" ', 1)
    return {"brand": icon["title"], "slug": slug, "ext": "svg", "bytes": svg.encode("utf-8"), "hex": "#" + icon["hex"],
            "source": f"{SI}/icons/{slug}.svg", "licence": "CC0-1.0 icon file (Simple Icons); the logo is a trademark of its owner",
            "brand_source": icon.get("source", "")}


def commons(brand):
    q = urllib.parse.quote(f"{brand} logo")
    api = ("https://commons.wikimedia.org/w/api.php?action=query&format=json&generator=search&gsrnamespace=6&gsrlimit=20"
           f"&gsrsearch={q}&prop=imageinfo&iiprop=url|extmetadata|mime")
    hit = commons_choice(brand, json.loads(get(api)).get("query", {}).get("pages", {}).values())
    if not hit:
        return None
    title, ii = hit
    lic = ii.get("extmetadata", {}).get("LicenseShortName", {}).get("value", "unknown")
    return {"brand": brand, "slug": slugify(brand), "ext": "svg" if ii["mime"] == "image/svg+xml" else "png", "bytes": get(ii["url"]),
            "hex": None, "source": ii.get("descriptionurl", ii["url"]),
            "licence": f"{lic} (Wikimedia Commons: {title}); the logo is a trademark of its owner", "brand_source": ""}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("brands", nargs="+")
    ap.add_argument("--project", required=True)
    a = ap.parse_args()
    out = pathlib.Path(a.project) / "art" / "logos"
    out.mkdir(parents=True, exist_ok=True)
    missing = []
    for brand in a.brands:
        hit = None
        for source in (simple_icons, commons):
            try:
                hit = source(brand)
            except Exception as e:                     # one source down must not stop the other
                print(f"{brand}: {source.__name__} failed ({e})", file=sys.stderr)
            if hit:
                break
        if not hit:
            missing.append(brand)
            continue
        f = out / f"{hit['slug']}.{hit['ext']}"
        f.write_bytes(hit["bytes"])
        meta = {k: hit[k] for k in ("brand", "source", "licence", "hex", "brand_source")}
        meta["fetched"] = datetime.date.today().isoformat()
        f.with_suffix(".json").write_text(json.dumps(meta, indent=1), encoding="utf-8")
        lic = pathlib.Path(a.project) / "licences.md"
        line = f"- Logo {hit['brand']}: `art/logos/{f.name}`, {hit['licence']}. Source: {hit['source']}\n"
        if not lic.exists() or line not in lic.read_text(encoding="utf-8"):
            with lic.open("a", encoding="utf-8") as fh:
                fh.write(line)
        comp = {"type": "logo", "id": hit["slug"], "x": 0, "y": 0, "w": 300, "src": f"art/logos/{f.name}", "label": hit["brand"]}
        print(f"{hit['brand']}: {f} ({len(hit['bytes'])} bytes, {hit['licence'].split(';')[0]})\n  {json.dumps(comp)}")
        if not hit["hex"]:
            print("  from Wikimedia Commons: LOOK at the file before using it (it must be the current logo of this brand)")
    if missing:
        sys.exit("not found: " + ", ".join(missing) + " (search the web for the brand's press page and add the file by hand)")


if __name__ == "__main__":
    main()
