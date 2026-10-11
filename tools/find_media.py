#!/usr/bin/env python3
"""Find and test original media from the GitHub runner (which can reach Wikimedia, NASA, EU sites...).

Job file jobs/find-<id>.json:
  {"id": "find-2026-10-12-x", "find": [
     {"commons": "Donald Tusk", "kind": "image"},        # Wikimedia Commons search, licence + author + direct URL
     {"commons": "European Parliament plenary", "kind": "video"},
     {"nasa": "Artemis II launch", "kind": "video"},       # NASA Image and Video Library (public domain)
     {"probe": "https://www.dvidshub.net/video/1015038", "in": 10, "dur": 6}   # can the renderer download it?
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
        print(f"    url: {ii.get('url')}")
        if desc:
            print(f"    about: {desc}")


def nasa(q, kind="video", limit=5):
    data = get_json("https://images-api.nasa.gov/search?" + urllib.parse.urlencode({"q": q, "media_type": kind}))
    for item in data.get("collection", {}).get("items", [])[:limit]:
        d = (item.get("data") or [{}])[0]
        files = get_json(item["href"]) if item.get("href") else []
        want = [f for f in files if re.search(r"~(orig|large|medium)\.(mp4|jpg)$", f)]
        print(f"- [OK to use - NASA, public domain] {d.get('title')}  {d.get('date_created', '')[:10]}  "
              f"center: {d.get('center')}")
        for f in want[:3]:
            print(f"    url: {f.replace('http://', 'https://')}")


def probe(src, a=0.0, dur=6.0):
    tmp = tempfile.mkdtemp()
    s = {"src": src, "type": "video"}
    try:
        if reel.is_page(s):
            reel.clip_info(src)
            path = reel.fetch_clip(src, tmp, a, a + dur)
        else:
            if re.search(r"//upload\.wikimedia\.org/", src):
                reel.commons_check(s)
            path = reel.fetch(src, tmp)
        out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                              "stream=width,height:format=duration", "-of", "csv=p=0", path],
                             capture_output=True, text=True).stdout.split()
        print(f"- [DOWNLOADS] {src} -> {' '.join(out)}")
    except SystemExit as e:
        print(f"- [FAILS] {src}: {e}")


def main(job_path):
    job = json.load(open(job_path))
    for q in job["find"]:
        print(f"\n## {json.dumps(q, ensure_ascii=False)}")
        try:
            if "commons" in q:
                commons(q["commons"], q.get("kind", "image"), q.get("limit", 8))
            elif "nasa" in q:
                nasa(q["nasa"], q.get("kind", "video"), q.get("limit", 5))
            elif "probe" in q:
                probe(q["probe"], float(q.get("in", 0)), float(q.get("dur", 6)))
        except Exception as e:
            print(f"- [ERROR] {e}")


if __name__ == "__main__":
    main(sys.argv[1])
