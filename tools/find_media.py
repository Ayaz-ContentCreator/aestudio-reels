#!/usr/bin/env python3
"""Find and test original media from the GitHub runner (which can reach Wikimedia, NASA, EU sites...).

Job file jobs/find-<id>.json:
  {"id": "find-2026-10-12-x", "find": [
     {"commons": "Donald Tusk", "kind": "image"},        # Wikimedia Commons search, licence + author + direct URL
     {"commons": "European Parliament plenary", "kind": "video"},
     {"nasa": "Artemis II launch", "kind": "video"},       # NASA Image and Video Library (public domain)
     {"probe": "https://www.dvidshub.net/video/1015038", "in": 10, "dur": 6},  # can the renderer download it?
     {"probe": "https://www.nbcnews.com/news/amp-video/mmvo42821701557", "sheet": true}  # + frame sheet (60 s)
  ]}
Results go to the release "<id>" as find.txt (one block per query). Only PD / CC0 / CC BY results are marked
"OK to use"; CC BY-SA is marked "SA" (avoid unless it is the only real image); everything else "NO".
"""
import json
import os
import re
import subprocess
import sys
import tempfile
import urllib.parse
import urllib.request

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "render"))
import reel  # noqa: E402

UA = reel.UA_BOT


def get_json(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=60) as r:
        return json.load(r)


def strip(html):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", html or "")).strip()


def verdict(lic):
    if reel.OK_LICENSE.search(lic or ""):
        return "OK to use"
    if reel.SA_LICENSE.search(lic or ""):
        return "SA (avoid unless only real image)"
    return "NO"


def commons(q, kind="image", limit=8):
    ft = "video" if kind == "video" else "bitmap"
    url = "https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode({
        "action": "query", "generator": "search", "gsrsearch": f"filetype:{ft} {q}", "gsrnamespace": 6,
        "gsrlimit": limit, "prop": "imageinfo", "iiprop": "url|size|mime|extmetadata",
        "format": "json"})
    pages = sorted(get_json(url).get("query", {}).get("pages", {}).values(), key=lambda p: p.get("index", 0))
    for p in pages:
        ii = (p.get("imageinfo") or [{}])[0]
        md = ii.get("extmetadata", {})
        lic = strip(md.get("LicenseShortName", {}).get("value"))
        who = strip(md.get("Artist", {}).get("value"))[:60]
        date = strip(md.get("DateTimeOriginal", {}).get("value"))[:20]
        desc = strip(md.get("ImageDescription", {}).get("value"))[:140]
        dur = f" {ii.get('duration', 0):.0f}s" if ii.get("duration") else ""
        print(f"- [{verdict(lic)}] {p['title']}  {ii.get('width')}x{ii.get('height')}{dur}  {lic}  by {who}  {date}")
        print(f"    url: {(ii.get('url') or '').split('?')[0]}")
        if desc:
            print(f"    about: {desc}")


def nasa(q, kind="video", limit=5):
    data = get_json("https://images-api.nasa.gov/search?" + urllib.parse.urlencode({"q": q, "media_type": kind}))
    for item in data.get("collection", {}).get("items", [])[:limit]:
        d = (item.get("data") or [{}])[0]
        href = urllib.parse.quote(item.get("href", ""), safe=":/~?=&%")
        files = get_json(href) if href else []
        want = [urllib.parse.quote(f, safe=":/~%") for f in files if re.search(r"~(orig|large|medium)\.(mp4|jpg)$", f)]
        print(f"- [OK to use - NASA, public domain] {d.get('title')}  {d.get('date_created', '')[:10]}  "
              f"center: {d.get('center')}")
        for f in want[:3]:
            print(f"    url: {f.replace('http://', 'https://')}")


def sheet(path, a, out_png):
    """Frames every 2 s with their source timecode, so the right seconds can be picked."""
    font = os.path.join(reel.FONTS, "InterDisplay-Bold.ttf").replace(":", "\\:")
    vf = (f"fps=1/2,scale=360:-2,drawtext=fontfile={font}:text='%{{pts\\:hms\\:{a:.0f}}}':x=10:y=10:"
          f"fontsize=26:fontcolor=white:box=1:boxcolor=black@0.6:boxborderw=6,tile=5x6:padding=4:color=0x202020")
    r = subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", path, "-vf", vf, "-frames:v", "1", "-q:v", "3", out_png],
                       capture_output=True, text=True)
    return r.returncode == 0


def probe(src, a=0.0, dur=6.0, sheet_png=None):
    tmp = tempfile.mkdtemp()
    s = {"src": src, "type": "video"}
    try:
        if reel.is_page(s):
            who = reel.clip_info(src)
            print(f"    credit would be: {who or '(set \"credit\" in the job)'}")
            path = reel.fetch_clip(src, tmp, a, a + dur)
        else:
            if re.search(r"//upload\.wikimedia\.org/", src):
                reel.commons_check(s)
            path = reel.fetch(src, tmp)
        out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                              "stream=width,height:format=duration", "-of", "csv=p=0", path],
                             capture_output=True, text=True).stdout.split()
        print(f"- [DOWNLOADS] {src} -> {' '.join(out)}")
        if sheet_png and sheet(path, a, sheet_png):
            print(f"    frames: {os.path.basename(sheet_png)} (every 2 s from {a:.0f}s; timecodes = source time)")
    except SystemExit as e:
        print(f"- [FAILS] {src}: {e}")


def main(job_path, outdir="."):
    job = json.load(open(job_path))
    for n, q in enumerate(job["find"], 1):
        print(f"\n## {json.dumps(q, ensure_ascii=False)}")
        try:
            if "commons" in q:
                commons(q["commons"], q.get("kind", "image"), q.get("limit", 8))
            elif "nasa" in q:
                nasa(q["nasa"], q.get("kind", "video"), q.get("limit", 5))
            elif "probe" in q:
                png = os.path.join(outdir, f"{job['id']}-{n}.jpg") if q.get("sheet") else None
                probe(q["probe"], float(q.get("in", 0)), float(q.get("dur", 60 if png else 6)), png)
        except Exception as e:
            print(f"- [ERROR] {e}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else ".")
