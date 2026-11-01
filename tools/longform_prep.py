#!/usr/bin/env python3
"""Prepare a long-form (16:9) video job: voiceover, word timings, scenes, media, music, render slices.

usage: longform_prep.py <longform/job.json> <outdir> [slots_dir]

Job: {"id", "format": "longform", "voice": {"tts": "kokoro", "voice": "am_michael", "speed": 1.03},
      "music": {"gen": "ambient", "gain_db": -24}, "tail": 8.0, "slices": 10,
      "beats": [{"say": "In [[1995|nineteen ninety-five]], ...", "show": {scene}, "pause": 0.4}, ...]}
"say" markup [[caption|spoken]]: the voice speaks the second part, captions show the first.
A beat without "show" continues the previous scene. Writes <outdir>/plan.json plus voice.wav, music.wav,
media/, geo/, words.json, chapters.txt, script.txt.
"""
import json
import math
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.parse
import urllib.request

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "render"))
import reel as R  # noqa: E402

FPS = 30
MARK = re.compile(r"\[\[([^|\]]*)\|([^\]]*)\]\]")
MODEL_DIR = os.environ.get("KOKORO_DIR", os.path.expanduser("~/kokoro"))
GEO = "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/"


def log(*a):
    print(*a, flush=True)


# ------------------------------------------------------------------ text
def parse(say):
    spoken, spans, pos = "", [], 0
    for m in MARK.finditer(say):
        spoken += say[pos:m.start()]
        a = len(spoken)
        spoken += m.group(2)
        spans.append((a, len(spoken), m.group(1)))
        pos = m.end()
    spoken += say[pos:]
    toks = [(mm.start(), mm.end()) for mm in re.finditer(r"\S+", spoken)]
    edits = []
    for a, b, cap in spans:
        idx = [i for i, (s, e) in enumerate(toks) if s < b and e > a]
        if not idx:
            continue
        i0, i1 = idx[0], idx[-1]
        pre, post = spoken[toks[i0][0]:a], spoken[b:toks[i1][1]]
        edits.append({"i": i0, "n": i1 - i0 + 1, "text": pre + cap + post, "em": True})
    return spoken, [spoken[s:e] for s, e in toks], edits


# ------------------------------------------------------------------ voice
def trim(a, sr, thr_db=-44, keep=0.04):
    win = int(sr * 0.01)
    if len(a) < win * 3:
        return a
    n = len(a) // win
    rms = np.sqrt(np.mean(a[:n * win].reshape(n, win) ** 2, axis=1) + 1e-12)
    on = np.where(20 * np.log10(rms) > thr_db)[0]
    if not len(on):
        return a
    s = max(0, on[0] * win - int(keep * sr))
    e = min(len(a), (on[-1] + 1) * win + int(keep * sr))
    return a[s:e]


def synth(beats, voice, outdir):
    from kokoro_onnx import Kokoro
    import soundfile as sf
    k = Kokoro(os.path.join(MODEL_DIR, "kokoro-v1.0.onnx"), os.path.join(MODEL_DIR, "voices-v1.0.bin"))
    sr = 24000
    lead = 0.6
    parts, t = [np.zeros(int(lead * sr), dtype=np.float32)], lead
    t_start = time.time()
    for i, bt in enumerate(beats):
        a, sr = k.create(bt["spoken"], voice=voice.get("voice", "am_michael"), speed=float(voice.get("speed", 1.0)),
                         lang=voice.get("lang", "en-us"))
        a = trim(np.asarray(a, dtype=np.float32), sr)
        bt["t0"] = round(t, 3)
        t += len(a) / sr
        bt["t1"] = round(t, 3)
        parts.append(a)
        pause = float(bt.get("pause", 0.44 if bt["spoken"].rstrip().endswith("?") else 0.30))
        parts.append(np.zeros(int(pause * sr), dtype=np.float32))
        t += pause
        if i % 20 == 0:
            log(f"  tts {i + 1}/{len(beats)}  {t:.1f}s audio  ({time.time() - t_start:.0f}s)")
    audio = np.concatenate(parts)
    sf.write(os.path.join(outdir, "voice.wav"), audio, sr)
    log(f"kokoro {voice.get('voice')}: {len(audio) / sr:.2f} s for {len(beats)} beats")
    return audio, sr


def align(beats, audio, sr, outdir):
    """Word timings: Whisper on the whole voiceover, aligned beat by beat to the known script."""
    ww = []
    try:
        from faster_whisper import WhisperModel
        n16 = int(len(audio) * 16000 / sr)
        a16 = np.interp(np.linspace(0, len(audio) - 1, n16), np.arange(len(audio)), audio).astype(np.float32)
        model = WhisperModel(os.environ.get("WHISPER_MODEL", "base.en"), device="cpu", compute_type="int8",
                             cpu_threads=os.cpu_count() or 4)
        t0 = time.time()
        segs, _ = model.transcribe(a16, language="en", word_timestamps=True, beam_size=1,
                                   condition_on_previous_text=False)
        ww = [{"text": w.word.strip(), "start": float(w.start), "end": float(w.end)}
              for seg in segs for w in (seg.words or []) if w.word.strip()]
        log(f"whisper: {len(ww)} words in {time.time() - t0:.0f}s")
    except Exception as e:  # pragma: no cover
        log(f"warning: whisper failed ({e}); estimating word timings")
    words = []
    for bt in beats:
        sub = [w for w in ww if w["start"] >= bt["t0"] - 0.3 and w["end"] <= bt["t1"] + 0.3]
        n = len(bt["words"])
        if sub:
            tw = R.align_script(bt["spoken"], sub)
        else:
            est = [max(len(R._norm(x)), 2) for x in bt["words"]]
            tot = sum(est)
            span = bt["t1"] - bt["t0"]
            tw, acc = [], bt["t0"]
            for x, e in zip(bt["words"], est):
                d = span * e / tot
                tw.append({"text": x, "start": acc, "end": acc + d})
                acc += d
        prev = bt["t0"]
        for w in tw[:n]:
            s = min(max(w["start"], prev, bt["t0"]), bt["t1"])
            e = min(max(w["end"], s + 0.04), bt["t1"])
            words.append({"text": w["text"], "start": round(s, 3), "end": round(e, 3)})
            prev = s
    json.dump(words, open(os.path.join(outdir, "words.json"), "w"), ensure_ascii=False)
    return words


# ------------------------------------------------------------------ media
def retry(fn, *a, tries=6, **kw):
    for k in range(tries):
        try:
            return fn(*a, **kw)
        except (SystemExit, Exception) as e:  # reel helpers raise SystemExit on HTTP errors
            if k == tries - 1 or "refused" in str(e):
                raise
            wait = 8 * (k + 1)
            log(f"  retry in {wait}s: {str(e)[:160]}")
            time.sleep(wait)


def prepare_image(path, outdir, name):
    from PIL import Image
    Image.MAX_IMAGE_PIXELS = None
    img = Image.open(path)
    img.load()
    if img.mode not in ("RGB",):
        img = img.convert("RGB")
    s = min(1.0, 3840 / max(img.width, img.height))
    if s < 1:
        img = img.resize((int(img.width * s), int(img.height * s)), Image.LANCZOS)
    out = os.path.join(outdir, "media", name + ".jpg")
    img.save(out, quality=92)
    return os.path.relpath(out, outdir)


def get_media(s, key, src, outdir, cache, kind, need):
    """Download/licence-check one source; returns relative path; may set credit."""
    name = R.hashlib.sha1(f"{src}|{s.get('in', 0)}|{need:.1f}".encode()).hexdigest()[:14]
    probe = {"src": src, "type": kind, "credit": s.get("credit") if key == "src" else None}
    if re.search(r"//upload\.wikimedia\.org/", src):
        retry(R.commons_check, probe)
        time.sleep(1.0)
    if kind == "video":
        a = float(s.get("in", 0))
        if R.remote_size(src) > 150e6:
            p = retry(R.fetch_section, src, cache, a, a + need + 1.5)
            s["in"] = 0.0
        else:
            p = retry(R.fetch, src, cache)
        out = os.path.join(outdir, "media", name + os.path.splitext(p)[1])
        shutil.copy(p, out)
        rel = os.path.relpath(out, outdir)
    else:
        p = retry(R.fetch, src, cache)
        rel = prepare_image(p, outdir, name)
    return rel, probe.get("credit")


def fetch_geo(outdir):
    d = os.path.join(outdir, "geo")
    os.makedirs(d, exist_ok=True)
    for name, f in (("land.geojson", "ne_50m_land.geojson"),
                    ("borders.geojson", "ne_50m_admin_0_boundary_lines_land.geojson"),
                    ("states.geojson", "ne_50m_admin_1_states_provinces_lines.geojson")):
        p = os.path.join(d, name)
        if not os.path.exists(p):
            retry(urllib.request.urlretrieve, GEO + f, p)
    log("geo data ready")


# ------------------------------------------------------------------ music (generated in code: no samples, no AI)
def ambient(path, seconds=64.0, sr=48000):
    """Quiet cinematic bed: slow minor-key pad (i-VI-III-VII-i-VI-iv-v) + soft low pulse. Loops seamlessly."""
    import soundfile as sf
    chords = [[45, 57, 60, 64, 69], [41, 53, 57, 60, 65], [48, 55, 60, 64, 67], [43, 55, 59, 62, 67],
              [45, 57, 60, 64, 69], [41, 53, 57, 60, 65], [38, 50, 57, 62, 65], [40, 52, 55, 59, 64]]
    n = int(seconds * sr)
    t = np.arange(n) / sr
    L = np.zeros(n, dtype=np.float64)
    Rr = np.zeros(n, dtype=np.float64)
    seg = seconds / len(chords)
    for ci, ch in enumerate(chords):
        c0 = ci * seg
        # circular envelope: 1.6 s attack, 2.5 s release overlapping the next chord (loops seamlessly)
        rel = (t - c0) % seconds
        env = np.where(rel < seg, np.minimum(1.0, rel / 1.6), 0.0)
        tail = rel - seg
        env = np.where((tail >= 0) & (tail < 2.5), 1 - tail / 2.5, env)
        env = env ** 1.5
        for ni, m in enumerate(ch):
            f = 440.0 * 2 ** ((m - 69) / 12)
            amp = (0.55 if ni == 0 else 0.30) / (1 + 0.15 * ni)
            for h in range(1, 5):
                ah = amp / h ** 1.9
                for det, side in ((-0.0011, 0), (0.0012, 1)):
                    wv = np.sin(2 * np.pi * f * h * (1 + det) * t + ni * 1.7 + h)
                    if side == 0:
                        L += ah * env * wv
                    else:
                        Rr += ah * env * wv
    # slow swell + low pulse (two soft hits per bar at 76 bpm)
    swell = 0.82 + 0.18 * np.sin(2 * np.pi * t / seconds * 2)
    beat = 60 / 76
    pulse = np.zeros(n)
    k = 0
    while k * beat * 2 < seconds:
        st = int(k * beat * 2 * sr)
        ln = int(0.9 * sr)
        tt = np.arange(min(ln, n - st)) / sr
        ci = int((k * beat * 2) // seg) % len(chords)
        f0 = 440.0 * 2 ** ((chords[ci][0] - 12 - 69) / 12)
        pulse[st:st + len(tt)] += 0.5 * np.exp(-tt * 5.5) * np.sin(2 * np.pi * f0 * tt)
        k += 1
    L = L * swell + pulse
    Rr = Rr * swell + pulse
    st = np.stack([L, Rr], 1)
    st /= np.max(np.abs(st)) / 0.7
    sf.write(path, st.astype(np.float32), sr)
    log(f"music bed: {seconds:.0f}s loop -> {path}")


# ------------------------------------------------------------------ real-footage slots
# Files supplied for a video, named by shot-list code: R01.jpg, R01b.jpg, R15.mp4 ... (one or more per code).
SLOT_FILE = re.compile(r"^(R\d{2})(?:[ _-]?([a-z]|\d{1,2}))?\.(jpe?g|png|webp|mp4|mov|mkv|webm|m4v)$", re.I)
VIDEO_EXT = ("mp4", "mov", "mkv", "webm", "m4v")
TO_FOOTAGE = {"headline", "statement", "quote", "versus"}   # these cards become footage + label when a slot exists
ON_FOOTAGE = {"photo", "video"}                              # these swap their source for the slot
SUB_MAX = 5.5                                                # footage scenes longer than this are split into cuts
ZOOMS = [(1.0, 1.08), (1.13, 1.05), (1.03, 1.11), (1.10, 1.02)]
FOCI = [(0.5, 0.5), (0.42, 0.45), (0.58, 0.5), (0.5, 0.4)]


def probe(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                        "stream=width,height:format=duration", "-of", "json", path], capture_output=True, text=True)
    j = json.loads(r.stdout or "{}")
    st = (j.get("streams") or [{}])[0]
    return float((j.get("format") or {}).get("duration") or 0), int(st.get("width") or 0), int(st.get("height") or 0)


def load_slots(d):
    slots = {}
    if not d or not os.path.isdir(d):
        return slots
    for f in sorted(os.listdir(d)):
        m = SLOT_FILE.match(f)
        if not m:
            continue
        p = os.path.join(d, f)
        it = {"file": p, "kind": "video" if m.group(3).lower() in VIDEO_EXT else "photo"}
        if it["kind"] == "video":
            it["dur"], w, h = probe(p)
            if it["dur"] <= 0.5:
                log(f"  slot {f}: unreadable video, skipped")
                continue
            it["pillar"] = bool(w and h and w / h < 1.3)
        slots.setdefault(m.group(1).upper(), []).append(it)
    log(f"slots: {len(slots)} codes, {sum(len(v) for v in slots.values())} files"
        + (f" ({', '.join(sorted(slots))})" if slots else ""))
    return slots


class Picker:
    """Hands out footage for each use of a slot: rotates photo variants and zooms, walks through a video so
    repeated uses show different moments (start points from job["slot_in"][code], a number or a list)."""

    def __init__(self, slots, slot_in, outdir):
        self.slots, self.slot_in, self.outdir = slots, slot_in or {}, outdir
        self.uses, self.cursor, self.idx, self.rel = {}, {}, {}, {}

    def _rel(self, it):
        if it["file"] not in self.rel:
            name = "slot_" + os.path.splitext(os.path.basename(it["file"]))[0]
            self.rel[it["file"]] = prepare_image(it["file"], self.outdir, name)
        return self.rel[it["file"]]

    def _in(self, code, it, need):
        ins = self.slot_in.get(code)
        ins = [float(x) for x in (ins if isinstance(ins, list) else [ins] if ins is not None else [])]
        dur = it["dur"]
        k = self.idx.get(code, 0)
        self.idx[code] = k + 1
        if k < len(ins):                       # chosen moments first, in order
            a = min(ins[k], max(0.0, dur - 1.0))
            self.cursor[it["file"]] = max(self.cursor.get(it["file"], 0.0), a + need + 0.4)
            return a
        first = min(2.0, dur * 0.08)
        c = self.cursor.get(it["file"], first)
        if c + need > dur - 0.2:
            c = first
        self.cursor[it["file"]] = c + need + 0.4
        return c

    def take(self, code, need):
        items = self.slots[code]
        k = self.uses.get(code, 0)
        self.uses[code] = k + 1
        it = items[k % len(items)]
        out = {"type": it["kind"], "slot": code}
        if it["kind"] == "photo":
            out["path"] = self._rel(it)
        elif need <= 0:
            out["file"] = it["file"]
        if it["kind"] == "photo":
            v = k // len(items)
            out["zoom"], out["focus"] = list(ZOOMS[v % len(ZOOMS)]), list(FOCI[v % len(FOCI)])
        else:
            a = round(self._in(code, it, need), 2)
            out["in"] = a
            if need > 0:      # keep only the seconds used (small plan artifact for the render jobs)
                out["path"], out["in"] = self._cut(it, code, a, need), 0.0
            if it["pillar"]:
                out["fit"] = "pillar"
        return out

    def _cut(self, it, code, a, need):
        out = os.path.join(self.outdir, "media", f"slot_{code}_{a:07.2f}_{need:.1f}.mp4")
        if not os.path.exists(out):
            r = subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{a:.3f}", "-i", it["file"], "-t",
                                f"{need + 0.6:.3f}", "-an", "-vf",
                                "scale='min(1920,iw)':'min(1080,ih)':force_original_aspect_ratio=decrease:"
                                "force_divisible_by=2", "-c:v", "libx264", "-preset", "veryfast", "-crf", "17",
                                "-pix_fmt", "yuv420p", out], capture_output=True, text=True)
            if r.returncode != 0:
                raise SystemExit(f"could not cut {it['file']} at {a:.1f}s: {r.stderr[-300:]}")
        return os.path.relpath(out, self.outdir)

    def still(self, code):
        """Background still for a card: the photo itself, or a frame grabbed from the video."""
        sh = self.take(code, 0.0)
        if sh["type"] == "photo":
            return sh["path"]
        src = sh.pop("file")
        out = os.path.join(self.outdir, "media", f"slot_{code}_still_{sh['in']:.1f}.jpg")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{sh['in'] + 0.5:.2f}", "-i", src, "-frames:v", "1",
                        "-q:v", "3", out], check=True)
        return os.path.relpath(out, self.outdir)


def card_label(s):
    t = s["type"]
    if t == "quote":
        return {"kicker": s.get("by"), "text": "“" + s["text"] + "”"}
    if t == "versus":
        return {"kicker": s.get("kicker"), "text": f"{s['left']} *vs* {s['right']}"}
    return {"kicker": s.get("kicker"), "text": s["text"]}


def apply_slots(scenes, slots, job, outdir):
    """Swap in the supplied real footage. Cards with words become footage + label (split into cuts);
    number/list/timeline cards keep their layout over a blurred still of the footage."""
    if not slots:
        return scenes
    pick = Picker(slots, job.get("slot_in"), outdir)
    credits = job.get("slot_credit", {})
    out, used, missing = [], 0, set()
    for s in scenes:
        code = s.get("slot")
        if not code:
            out.append(s)
            continue
        if code not in slots:
            missing.add(code)
            out.append(s)
            continue
        used += 1
        cr = credits.get(code, "")
        if s["type"] in TO_FOOTAGE or s["type"] in ON_FOOTAGE:
            label = card_label(s) if s["type"] in TO_FOOTAGE else s.get("label")
            dur = s["end"] - s["start"]
            n = max(1, math.ceil(dur / SUB_MAX - 0.09))
            step = dur / n
            for j in range(n):
                a = s["start"] + j * step
                b = s["end"] if j == n - 1 else s["start"] + (j + 1) * step
                sh = pick.take(code, b - a)
                sh.update({"start": round(a, 3), "end": round(b, 3), "credit": cr})
                if j == 0 and label:
                    sh["label"] = label
                out.append(sh)
        else:
            s = dict(s)
            s.pop("bg", None)
            s["bg_path"] = pick.still(code)
            s["credit"] = cr
            out.append(s)
    log(f"slots: {used} scenes use supplied footage; no file for {', '.join(sorted(missing)) or 'none'}")
    return out


# ------------------------------------------------------------------ main
def fmt_ts(sec):
    sec = int(sec)
    return f"{sec // 3600}:{sec % 3600 // 60:02d}:{sec % 60:02d}" if sec >= 3600 else f"{sec // 60}:{sec % 60:02d}"


def main(job_path, outdir, slots_dir=None):
    job = json.load(open(job_path))
    os.makedirs(os.path.join(outdir, "media"), exist_ok=True)
    cache = os.path.join(outdir, "..", ".cache")
    beats = job["beats"]
    words_all, edits_all = [], []
    for bt in beats:
        spoken, words, edits = parse(bt["say"])
        bt["spoken"], bt["words"] = spoken, words
        for e in edits:
            e = dict(e)
            e["i"] += len(words_all)
            edits_all.append(e)
        words_all += words
    script = " ".join(bt["spoken"] for bt in beats)
    open(os.path.join(outdir, "script.txt"), "w").write(script + "\n")
    log(f"{len(beats)} beats, {len(words_all)} spoken words")

    audio, sr = synth(beats, job.get("voice", {}), outdir)
    words = align(beats, audio, sr, outdir)
    tokens = R.build_tokens({"words": words, "display": edits_all, "emphasis": job.get("emphasis", [])})
    voice_len = len(audio) / sr
    total = round(voice_len + float(job.get("tail", 8.0)), 2)

    scenes = []
    for bt in beats:
        if "show" in bt:
            s = dict(bt["show"])
            s["start"] = round(max(0.0, bt["t0"] - 0.12), 3) if scenes else 0.0
            scenes.append(s)
    for i, s in enumerate(scenes):
        s["end"] = scenes[i + 1]["start"] if i + 1 < len(scenes) else total

    punct = re.compile(r"\*([^*]+)\*([.,!?:;…]+)")
    for s in scenes:                    # keep punctuation inside accent markup: "*word*." -> "*word.*"
        for key in ("text", "title"):
            if isinstance(s.get(key), str):
                s[key] = punct.sub(r"*\1\2*", s[key])
        if isinstance(s.get("label"), dict) and s["label"].get("text"):
            s["label"]["text"] = punct.sub(r"*\1\2*", s["label"]["text"])
    slots = load_slots(slots_dir)
    scenes = apply_slots(scenes, slots, job, outdir)
    for i, s in enumerate(scenes):
        need = s["end"] - s["start"]
        if s.get("src") and not s.get("path"):
            s["path"], cr = get_media(s, "src", s["src"], outdir, cache, s["type"], need)
            if cr and not s.get("credit"):
                s["credit"] = cr
        if s.get("bg") and not s.get("bg_path"):
            s["bg_path"], cr = get_media(s, "bg", s["bg"], outdir, cache, "photo", need)
            if cr and not s.get("credit"):
                s["credit"] = cr
        log(f"  scene {i:3d} {s['start']:7.2f}-{s['end']:7.2f} {s['type']:9s} {s.get('slot', ''):4s} "
            f"{(s.get('credit') or '')[:60]}")
    if any(s["type"] == "map" for s in scenes):
        fetch_geo(outdir)

    music = job.get("music") or {}
    if music.get("gen") == "ambient":
        ambient(os.path.join(outdir, "music.wav"))
    elif music.get("url"):
        shutil.copy(R.fetch(music["url"], cache), os.path.join(outdir, "music.wav"))

    # slices of roughly equal duration, cut at scene boundaries
    k = int(job.get("slices", 10))
    target = total / k
    slices, cur0, acc = [], 0, 0.0
    for i, s in enumerate(scenes):
        acc += s["end"] - s["start"]
        if acc >= target * (len(slices) + 1) and len(slices) < k - 1 and i < len(scenes) - 1:
            f = int(round(s["end"] * FPS))
            slices.append([cur0, f])
            cur0 = f
    slices.append([cur0, int(round(total * FPS))])

    chapters = [("Intro", 0.0)] + [(f"{s['num']}. {s['title']}", s["start"]) for s in scenes if s["type"] == "chapter"]
    open(os.path.join(outdir, "chapters.txt"), "w").write(
        "\n".join(f"{fmt_ts(t)} {name}" for name, t in chapters) + "\n")

    plan = {"id": job["id"], "fps": FPS, "w": 1920, "h": 1080, "total": total, "voice_len": round(voice_len, 2),
            "voice": "voice.wav", "music": "music.wav" if os.path.exists(os.path.join(outdir, "music.wav")) else None,
            "music_gain_db": float(music.get("gain_db", -24)), "scenes": scenes, "tokens": tokens,
            "slices": slices, "title": job.get("title", ""), "thumbnail": job.get("thumbnail", {})}
    th = plan["thumbnail"]
    if th.get("slot") and th["slot"] in slots:
        th["bg_path"] = Picker(slots, job.get("slot_in"), outdir).still(th["slot"])
    elif th.get("bg"):
        th["bg_path"], _ = get_media({"type": "photo"}, "bg", th["bg"], outdir, cache, "photo", 1)
    json.dump(plan, open(os.path.join(outdir, "plan.json"), "w"), ensure_ascii=False)
    log(f"plan: {len(scenes)} scenes, {total:.1f}s ({fmt_ts(total)}), {len(slices)} slices: "
        + ", ".join(f"{(b - a) / FPS:.0f}s" for a, b in slices))
    log("chapters:\n" + open(os.path.join(outdir, "chapters.txt")).read())


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None)
