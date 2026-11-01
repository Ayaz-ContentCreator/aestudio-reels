#!/usr/bin/env python3
"""Download supplied footage from Google Drive (files shared "anyone with the link") for a long-form video.

usage: fetch_media.py <longform/media/<id>.json> <slots_dir> <sheets_dir>

List: {"id": "...", "files": [{"drive": "<file id>", "name": "R01.jpg"}, ...]}
Photos are re-saved as JPEG (any format Pillow reads); videos are kept as they are and checked with ffprobe.
For every video a contact sheet sheets_dir/sheet-<code>.jpg shows one frame every few seconds, with timestamps,
to choose in-points (job["slot_in"]).
"""
import json
import math
import os
import subprocess
import sys

import gdown
from PIL import Image, ImageDraw, ImageFont

Image.MAX_IMAGE_PIXELS = None
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def probe(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                        "stream=width,height,codec_type:format=duration", "-of", "json", path],
                       capture_output=True, text=True)
    j = json.loads(r.stdout or "{}")
    st = (j.get("streams") or [{}])[0]
    return float((j.get("format") or {}).get("duration") or 0), int(st.get("width") or 0), int(st.get("height") or 0)


def sheet(path, code, outdir, cols=6, tw=320, th=180, most=48):
    dur, w, h = probe(path)
    step = max(2, math.ceil(dur / most))
    times = [step / 2 + k * step for k in range(int(dur // step))] or [0.0]
    rows = math.ceil(len(times) / cols)
    img = Image.new("RGB", (cols * tw, rows * th + 40), (12, 12, 14))
    d = ImageDraw.Draw(img)
    f = ImageFont.truetype(FONT, 18)
    d.text((8, 10), f"{code}  {os.path.basename(path)}  {dur:.1f}s  {w}x{h}", font=f, fill=(255, 210, 63))
    for i, t in enumerate(times):
        r = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.2f}", "-i", path, "-frames:v", "1",
                            "-vf", f"scale={tw}:{th}:force_original_aspect_ratio=decrease,pad={tw}:{th}:-1:-1",
                            "-f", "image2pipe", "-vcodec", "png", "-"], capture_output=True)
        x, y = (i % cols) * tw, (i // cols) * th + 40
        if r.stdout:
            from io import BytesIO
            img.paste(Image.open(BytesIO(r.stdout)).convert("RGB"), (x, y))
        d.rectangle((x, y, x + 74, y + 24), fill=(0, 0, 0))
        d.text((x + 5, y + 3), f"{int(t // 60)}:{t % 60:04.1f}", font=f, fill=(255, 255, 255))
    out = os.path.join(outdir, f"sheet-{code}.jpg")
    img.save(out, quality=82)
    return out


def main(list_path, slots, sheets):
    job = json.load(open(list_path))
    os.makedirs(slots, exist_ok=True)
    os.makedirs(sheets, exist_ok=True)
    ok, bad = [], []
    for f in job["files"]:
        name = f["name"]
        stem, ext = os.path.splitext(name)
        tmp = os.path.join(slots, ".dl_" + name)
        try:
            gdown.download(id=f["drive"], output=tmp, quiet=True)
            if not os.path.exists(tmp) or os.path.getsize(tmp) < 1000:
                raise RuntimeError("empty download (is the file shared 'anyone with the link'?)")
            try:
                im = Image.open(tmp)
                im.load()
                out = os.path.join(slots, stem + ".jpg")
                im.convert("RGB").save(out, quality=93)
                os.remove(tmp)
                ok.append(f"{name}: photo {im.width}x{im.height}")
                continue
            except Exception:
                pass
            dur, w, h = probe(tmp)
            if dur <= 0.3 or not w:
                raise RuntimeError("not a readable photo or video")
            vext = ext.lower() if ext.lower() in (".mp4", ".mov", ".mkv", ".webm", ".m4v") else ".mp4"
            out = os.path.join(slots, stem + vext)
            os.replace(tmp, out)
            sheet(out, stem, sheets)
            ok.append(f"{name}: video {dur:.1f}s {w}x{h}")
        except Exception as e:
            bad.append(f"{name}: {e}")
            if os.path.exists(tmp):
                os.remove(tmp)
    print("OK:\n  " + "\n  ".join(ok))
    if bad:
        print("FAILED:\n  " + "\n  ".join(bad))
    if not ok:
        sys.exit("nothing downloaded")


if __name__ == "__main__":
    main(*sys.argv[1:4])
