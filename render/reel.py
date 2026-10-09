#!/usr/bin/env python3
"""AE Studio Reel renderer: job JSON -> 1080x1920 H.264 MP4.

    python3 render/reel.py JOB.json OUT.mp4
    python3 render/reel.py JOB.json OUT_DIR --stills 0.4,5.1,19.0   # QA stills (PNG)

Job format: see README.md. Remote media (http/https) is downloaded to a cache
next to the output; local paths are used as-is (handy for tests).
"""
import argparse
import hashlib
import itertools
import json
import math
import os
import re
import subprocess
import sys
import urllib.request

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont
import numpy as np

W, H, FPS = 1080, 1920, 30
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONTS = os.path.join(ROOT, "assets", "fonts")

# ------------------------------------------------------------------ design tokens
ACCENT = (255, 210, 63)          # warm news yellow
WHITE = (255, 255, 255)
SOFT = (226, 228, 232)           # secondary text
INK = (14, 14, 16)               # text on accent
MARGIN = 84                      # editorial left/right margin
TITLE_TOP = 300                  # top of title blocks (clear of the app's top bar)
CAP_BASE = 1262                  # caption baseline (clear of the bottom UI)
CAP_SIZE = 68
CAP_MAXW = 820                   # keeps captions clear of the right-side buttons
HOOK_SIZE = 104
LABEL_SIZE = 78

BLACK = "InterDisplay-Black.ttf"
XBOLD = "InterDisplay-ExtraBold.ttf"
BOLD = "InterDisplay-Bold.ttf"
SEMI = "InterDisplay-SemiBold.ttf"
MONO = "JetBrainsMono-ExtraBold.ttf"
MONO_B = "JetBrainsMono-Bold.ttf"

_fonts = {}
try:
    from PIL import features as _features
    _LAYOUT = ImageFont.Layout.RAQM if _features.check("raqm") else ImageFont.Layout.BASIC
except Exception:  # pragma: no cover
    _LAYOUT = ImageFont.Layout.BASIC
if _LAYOUT != ImageFont.Layout.RAQM:
    print("warning: libraqm not available - kerning will be basic", file=sys.stderr)


def font(name, size):
    key = (name, int(round(size)))
    if key not in _fonts:
        _fonts[key] = ImageFont.truetype(os.path.join(FONTS, name), key[1], layout_engine=_LAYOUT)
    return _fonts[key]


def cap_height(f):
    return -f.getbbox("H", anchor="ls")[1]


def text_w(f, s, tr=0.0):
    return f.getlength(s) + tr * max(len(s) - 1, 0)


def draw_text(d, x, y, s, f, fill, tr=0.0, features=None):
    """Left edge at x, baseline at y. tr = extra tracking in px."""
    if not tr:
        d.text((x, y), s, font=f, fill=fill, anchor="ls", features=features)
        return
    for i, ch in enumerate(s):
        d.text((x + f.getlength(s[:i]) + tr * i, y), ch, font=f, fill=fill, anchor="ls")


# ------------------------------------------------------------------ easing
def clamp(v, lo=0.0, hi=1.0):
    return lo if v < lo else hi if v > hi else v


def ease_out_cubic(p):
    p = clamp(p)
    return 1 - (1 - p) ** 3


def ease_out_expo(p):
    p = clamp(p)
    return 1.0 if p >= 1 else 1 - 2 ** (-10 * p)


def ease_in_out(p):
    p = clamp(p)
    return p * p * (3 - 2 * p)


def lerp(a, b, t):
    return a + (b - a) * t


# ------------------------------------------------------------------ sprites
def with_opacity(img, op):
    if op >= 0.999:
        return img
    if op <= 0.002:
        return None
    out = img.copy()
    out.putalpha(img.getchannel("A").point(lambda v: int(v * op)))
    return out


def blit(canvas, sprite, x, y, op=1.0):
    if sprite is None:
        return
    sprite = with_opacity(sprite, op)
    if sprite is None:
        return
    x, y = int(round(x)), int(round(y))
    sx0, sy0 = max(0, -x), max(0, -y)
    sx1, sy1 = min(sprite.width, W - x), min(sprite.height, H - y)
    if sx1 <= sx0 or sy1 <= sy0:
        return
    if (sx0, sy0, sx1, sy1) != (0, 0, sprite.width, sprite.height):
        sprite = sprite.crop((sx0, sy0, sx1, sy1))
    canvas.alpha_composite(sprite, (x + sx0, y + sy0))


def shadowed(size, ops, shadows=((0, 6, 16, 0.55), (0, 2, 3, 0.30))):
    """Render text ops [(x, y, s, font, rgb, tracking)] into an RGBA sprite with soft shadows."""
    w, h = size
    txt = Image.new("RGBA", size, (0, 0, 0, 0))
    mask = Image.new("L", size, 0)
    dt, dm = ImageDraw.Draw(txt), ImageDraw.Draw(mask)
    for x, y, s, f, rgb, tr in ops:
        draw_text(dt, x, y, s, f, tuple(rgb) + (255,), tr)
        draw_text(dm, x, y, s, f, 255, tr)
    out = Image.new("RGBA", size, (0, 0, 0, 0))
    for ox, oy, blur, op in shadows:
        m = Image.new("L", size, 0)
        m.paste(mask, (ox, oy))
        m = m.filter(ImageFilter.GaussianBlur(blur)).point(lambda v, op=op: int(v * op))
        layer = Image.new("RGBA", size, (0, 0, 0, 0))
        layer.putalpha(m)
        out = Image.alpha_composite(out, layer)
    return Image.alpha_composite(out, txt)


def aa_rrect(size, box, radius, ss=4):
    """Anti-aliased rounded-rectangle mask (L) on a canvas of `size`; box in float px."""
    x0, y0, x1, y1 = box
    bx0, by0 = int(math.floor(x0)) - 1, int(math.floor(y0)) - 1
    bx1, by1 = int(math.ceil(x1)) + 1, int(math.ceil(y1)) + 1
    big = Image.new("L", ((bx1 - bx0) * ss, (by1 - by0) * ss), 0)
    ImageDraw.Draw(big).rounded_rectangle(
        ((x0 - bx0) * ss, (y0 - by0) * ss, (x1 - bx0) * ss, (y1 - by0) * ss),
        radius=min(radius, (y1 - y0) / 2, (x1 - x0) / 2) * ss, fill=255)
    m = Image.new("L", size, 0)
    m.paste(big.resize((bx1 - bx0, by1 - by0), Image.LANCZOS), (bx0, by0))
    return m


def vgrad(h, top_a, bottom_a, power=1.6):
    t = np.linspace(0.0, 1.0, h)[:, None]
    if top_a > bottom_a:
        a = bottom_a + (top_a - bottom_a) * (1 - t) ** power
    else:
        a = top_a + (bottom_a - top_a) * t ** power
    arr = np.zeros((h, W, 4), dtype=np.uint8)
    arr[..., 3] = np.repeat((a * 255).astype(np.uint8), W, axis=1)
    return Image.fromarray(arr, "RGBA")


def card_shade():
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    r = np.sqrt(((xx - W / 2) / (W * 0.75)) ** 2 + ((yy - H * 0.45) / (H * 0.62)) ** 2)
    a = 0.40 + 0.38 * np.clip(r, 0, 1) ** 2
    arr = np.zeros((H, W, 4), dtype=np.uint8)
    arr[..., 3] = (np.clip(a, 0, 1) * 255).astype(np.uint8)
    return Image.fromarray(arr, "RGBA")


TOP_SCRIM = vgrad(980, 0.72, 0.0, power=1.5)
BOTTOM_SCRIM = vgrad(1000, 0.0, 0.58, power=1.5)
CARD_SHADE = None  # built lazily


# ------------------------------------------------------------------ text layout
def parse_markup(text):
    """'Rent has *almost doubled*' -> [(word, accent?)]"""
    out = []
    for i, seg in enumerate(text.split("*")):
        out += [(w, i % 2 == 1) for w in seg.split()]
    return out


FUNC = set("a an the of in on at to for from by with and or but nor as than his her their its our your my "
           "this that these those into onto over under about across after before until while if so".split())


def _bare(w):
    return re.sub(r"[^\w'-]", "", w).lower()


def wrap_tokens(tokens, f, maxw, max_lines=3, tr=0.0):
    words = [w for w, _ in tokens]
    n = len(words)

    def width(a, b):
        return text_w(f, " ".join(words[a:b]), tr)

    for k in range(1, max_lines + 1):
        best = None
        for br in itertools.combinations(range(1, n), k - 1):
            idx = (0,) + br + (n,)
            ws = [width(idx[i], idx[i + 1]) for i in range(k)]
            longest = max(ws)
            if longest > maxw:
                continue
            score = longest
            for i in range(k):
                count = idx[i + 1] - idx[i]
                short = longest - ws[i]
                if i < k - 1:
                    score += short * short / longest * 0.9      # ragged middle/first lines
                if count == 1 and k > 1 and len(words[idx[i]]) <= 9:
                    score += 0.35 * maxw                        # lone short word on a line
                if i < k - 1 and _bare(words[idx[i + 1] - 1]) in FUNC:
                    score += 0.30 * maxw                        # line ending on "a", "of", "in"...
                if i < k - 1 and re.search(r"\d", words[idx[i + 1] - 1]) and words[idx[i + 1]][:1].islower():
                    score += 0.30 * maxw                        # keep "10 years" together
            if k > 1 and ws[-1] > ws[0] * 1.25:
                score += 0.05 * maxw                            # prefer a top-heavy rag
            if best is None or score < best[0]:
                best = (score, idx)
        if best:
            idx = best[1]
            return [tokens[idx[i]:idx[i + 1]] for i in range(len(idx) - 1)]
    lines, cur = [], []
    for t in tokens:
        if cur and text_w(f, " ".join(w for w, _ in cur + [t]), tr) > maxw:
            lines.append(cur)
            cur = []
        cur.append(t)
    return lines + ([cur] if cur else [])


def fit_size(name, text, maxw, start, minimum):
    s = start
    while s > minimum and text_w(font(name, s), text) > maxw:
        s -= 2
    return s


class Kicker:
    """Small accent square + tracked mono caps, e.g. '■ SPAIN · HOUSING'."""

    def __init__(self, text, size=30):
        self.f = font(MONO, size)
        self.text = text.upper()
        self.tr = size * 0.08
        capk = cap_height(self.f)
        sq = round(size * 0.42)
        pad = 24
        tw_ = text_w(self.f, self.text, self.tr)
        self.w = int(sq + 18 + tw_ + 2 * pad)
        self.h = int(capk + 2 * pad + 10)
        self.base = pad + capk
        img = shadowed((self.w, self.h), [(pad + sq + 18, self.base, self.text, self.f, ACCENT, self.tr)],
                       shadows=((0, 3, 8, 0.5),))
        d = ImageDraw.Draw(img)
        d.rectangle((pad, self.base - capk + (capk - sq) / 2, pad + sq, self.base - capk + (capk - sq) / 2 + sq),
                    fill=ACCENT + (255,))
        self.img = img
        self.pad = pad
        self.cap = capk


class TextBlock:
    """Left-aligned multi-line headline split into per-line sprites (for reveal animation)."""

    def __init__(self, text, fname, size, maxw, max_lines=3, color=WHITE, leading=1.04, shadow=True):
        self.f = font(fname, size)
        toks = parse_markup(text)
        self.lines = wrap_tokens(toks, self.f, maxw, max_lines)
        self.cap = cap_height(self.f)
        self.pitch = round(size * leading)
        self.pad = 36
        self.sprites = []
        space = self.f.getlength(" ")
        for line in self.lines:
            lw = text_w(self.f, " ".join(w for w, _ in line))
            sw, sh = int(lw + 2 * self.pad), int(self.cap + self.pad * 2 + size * 0.28)
            ops, x = [], self.pad
            for w, acc in line:
                ops.append((x, self.pad + self.cap, w, self.f, ACCENT if acc else color, 0))
                x += self.f.getlength(w) + space
            shadows = ((0, 6, 18, 0.50), (0, 2, 3, 0.28)) if shadow else ()
            self.sprites.append(shadowed((sw, sh), ops, shadows))
        self.height = self.cap + self.pitch * (len(self.lines) - 1)   # cap top -> last baseline

    def draw(self, canvas, x, top, lt, out=1.0, stagger=0.07, dur=0.5, delay=0.0):
        """Reveal each line upward from behind its own baseline; x,top = cap-top-left of line 1."""
        for i, sp in enumerate(self.sprites):
            p = ease_out_expo((lt - delay - stagger * i) / dur)
            if p <= 0:
                continue
            off = (1 - p) * self.pitch * 0.6
            vis = int(round(sp.height - off))
            if vis <= 0:
                continue
            spc = sp.crop((0, 0, sp.width, vis)) if vis < sp.height else sp
            y = top + i * self.pitch - self.pad
            blit(canvas, spc, x - self.pad, y + off - (1 - out) * 12, min(1.0, p * 1.5) * out)


# ------------------------------------------------------------------ captions
class Captions:
    def __init__(self, tokens, hide):
        self.f = font(XBOLD, CAP_SIZE)
        self.space = self.f.getlength(" ") + 8
        self.cap = cap_height(self.f)
        self.hide = hide
        self.phrases = self._phrases(tokens)
        self._cache = {}

    def _phrases(self, toks):
        # split into segments at punctuation / pauses, then segment each optimally
        segs, cur = [], []
        for w in toks:
            if cur and w["start"] - cur[-1]["end"] > 0.45:
                segs.append(cur)
                cur = []
            cur.append(w)
            if re.search(r"[.?!,;:]$", w["raw"]):
                segs.append(cur)
                cur = []
        if cur:
            segs.append(cur)
        groups = []
        for seg in segs:
            groups += self._segment(seg)
        out = []
        for k, g in enumerate(groups):
            t0 = max(0.0, g[0]["start"] - 0.05)
            t1 = g[-1]["end"] + 0.30
            if k + 1 < len(groups):
                nxt = groups[k + 1][0]["start"] - 0.05
                t1 = nxt if nxt - g[-1]["end"] < 0.7 else min(t1, nxt)
            out.append({"words": g, "t0": t0, "t1": t1})
        return out

    def _cost(self, seg, a, b):
        g = seg[a:b]
        if len(g) > 4 or text_w(self.f, " ".join(w["text"] for w in g)) + self.space * 0 > CAP_MAXW:
            return None
        d = g[-1]["end"] - g[0]["start"]
        c = 1.0 + max(0.0, 0.55 - d) * 4 + max(0.0, d - 1.9) * 2
        if len(g) == 1 and len(seg) > 1:
            c += 1.4
        if b < len(seg):
            last, nxt = g[-1]["text"], seg[b]["text"]
            if _bare(last) in FUNC:
                c += 2.0
            if last[:1].isupper() and nxt[:1].isupper():
                c += 2.5                                   # don't split names ("Pedro | Sanchez")
                after = seg[b + 1]["text"][:1].isupper() if b + 1 < len(seg) else False
                if not after:
                    c += 1.5                               # never strand a surname
            if re.search(r"\d", last) and nxt[:1].islower():
                c += 1.5                                   # keep "10 years" together
        return c

    def _segment(self, seg):
        n = len(seg)
        best = [0.0] + [math.inf] * n
        back = [0] * (n + 1)
        for i in range(1, n + 1):
            for j in range(max(0, i - 4), i):
                c = self._cost(seg, j, i)
                if c is not None and best[j] + c < best[i]:
                    best[i], back[i] = best[j] + c, j
            if best[i] == math.inf:                       # single over-wide word
                best[i], back[i] = best[i - 1] + 1, i - 1
        out, i = [], n
        while i > 0:
            out.append(seg[back[i]:i])
            i = back[i]
        return out[::-1]

    def _sprite(self, k):
        if k in self._cache:
            return self._cache[k]
        g = self.phrases[k]["words"]
        widths = [self.f.getlength(w["text"]) for w in g]
        total = sum(widths) + self.space * (len(g) - 1)
        pad = 44
        sw, sh = int(total + 2 * pad), int(self.cap + 2 * pad + CAP_SIZE * 0.3)
        base = pad + self.cap
        ops, dark_ops, boxes, x = [], [], [], pad
        for w, wd in zip(g, widths):
            ops.append((x, base, w["text"], self.f, ACCENT if w.get("em") else WHITE, 0))
            dark_ops.append((x, base, w["text"]))
            boxes.append((x, wd))
            x += wd + self.space
        white = shadowed((sw, sh), ops, ((0, 6, 16, 0.62), (0, 2, 3, 0.40)))
        dark = Image.new("RGBA", (sw, sh), (0, 0, 0, 0))
        dd = ImageDraw.Draw(dark)
        for x0, y0, s in dark_ops:
            draw_text(dd, x0, y0, s, self.f, INK + (255,))
        res = {"white": white, "dark": dark, "boxes": boxes, "base": base,
               "x": W / 2 - sw / 2, "y": CAP_BASE - base}
        self._cache[k] = res
        return res

    def draw(self, canvas, t):
        if any(a <= t < b for a, b in self.hide):
            return
        k = next((i for i, p in enumerate(self.phrases) if p["t0"] <= t < p["t1"]), None)
        if k is None:
            return
        ph, sp = self.phrases[k], self._sprite(k)
        lt = t - ph["t0"]
        p = ease_out_cubic(lt / 0.14)
        words = ph["words"]
        ai = 0
        for i, w in enumerate(words):
            if t >= w["start"] - 0.04:
                ai = i

        def box(i):
            bx, wd = sp["boxes"][i]
            return (bx - 13, sp["base"] - self.cap - 16, bx + wd + 13, sp["base"] + 18)

        b1 = box(ai)
        q = ease_out_cubic((t - (words[ai]["start"] - 0.04)) / 0.08)
        if ai > 0:
            b0 = box(ai - 1)
            b = tuple(lerp(b0[j], b1[j], q) for j in range(4))
        else:
            s = lerp(0.85, 1.0, q)
            cx, cy = (b1[0] + b1[2]) / 2, (b1[1] + b1[3]) / 2
            hw, hh = (b1[2] - b1[0]) / 2 * s, (b1[3] - b1[1]) / 2 * s
            b = (cx - hw, cy - hh, cx + hw, cy + hh)
        layer = sp["white"].copy()
        m = aa_rrect(layer.size, b, 14)
        boxl = Image.new("RGBA", layer.size, ACCENT + (0,))
        boxl.putalpha(m)
        layer.alpha_composite(boxl)
        dk = sp["dark"].copy()
        dk.putalpha(ImageChops.multiply(sp["dark"].getchannel("A"), m))
        layer.alpha_composite(dk)
        blit(canvas, layer, sp["x"], sp["y"] + (1 - p) * 16, p)


# ------------------------------------------------------------------ titles (over footage)
class Title:
    def __init__(self, spec):
        self.t0, self.t1 = float(spec["start"]), float(spec["end"])
        self.hook = spec.get("style", "label") == "hook"
        self.lead = 0.45 if (self.hook and self.t0 == 0) else 0.0   # first frame already shows the hook
        size = HOOK_SIZE if self.hook else LABEL_SIZE
        self.block = TextBlock(spec["text"], BLACK, size, W - 2 * MARGIN, max_lines=3)
        self.kicker = Kicker(spec["kicker"], 36 if self.hook else 33) if spec.get("kicker") else None

    def draw(self, canvas, t):
        if not (self.t0 <= t < self.t1):
            return
        lt = t - self.t0 + self.lead
        out = ease_out_cubic((self.t1 - t) / 0.22)
        blit(canvas, TOP_SCRIM, 0, 0, ease_out_cubic(lt / 0.3) * out)
        top = TITLE_TOP
        if self.kicker:
            k = self.kicker
            pk = ease_out_cubic(lt / 0.35)
            blit(canvas, k.img, MARGIN - k.pad - (1 - pk) * 18, top - k.pad - (1 - out) * 12, pk * out)
            top += k.cap + 30
        self.block.draw(canvas, MARGIN, top, lt, out, delay=0.06)


# ------------------------------------------------------------------ cards (full-frame typography)
class Card:
    def __init__(self, spec):
        self.s = spec
        self.kind = spec.get("card", "headline")
        self.kicker = Kicker(spec["kicker"], 34) if spec.get("kicker") else None
        maxw = W - 2 * MARGIN
        if self.kind == "headline":
            self.head = TextBlock(spec["text"], BLACK, spec.get("size", 128), maxw, max_lines=3, leading=1.0)
            self.sub = TextBlock(spec["sub"], SEMI, 48, maxw, max_lines=2, color=SOFT) if spec.get("sub") else None
        elif self.kind == "stat":
            self.value = float(spec["value"])
            self.decimals = int(spec.get("decimals", 0))
            self.prefix, self.suffix = spec.get("prefix", ""), spec.get("suffix", "")
            final = self._fmt(self.value)
            self.nsize = fit_size(BLACK, final, maxw, 300, 120)
            self.nf = font(BLACK, self.nsize)
            self.ncap = cap_height(self.nf)
            self.sub = TextBlock(spec["sub"], BOLD, 56, maxw, max_lines=2) if spec.get("sub") else None
            self.source = spec.get("source")
        elif self.kind == "end":
            self.head = TextBlock(spec["text"], BLACK, spec.get("size", 112), maxw, max_lines=4, leading=1.0)
            self.cta = spec.get("cta", "Tell us below ↓")
            self.follow = spec.get("follow", "")

    def _fmt(self, v):
        s = f"{v:,.{self.decimals}f}"
        return f"{self.prefix}{s}{self.suffix}"

    def _layout_top(self, block_h):
        return int(870 - block_h / 2)

    def draw(self, canvas, lt, dur):
        out = ease_out_cubic((dur - lt) / 0.2)
        if self.kind == "headline":
            h = (self.kicker.cap + 34 if self.kicker else 0) + self.head.height + (
                60 + self.sub.height if self.sub else 0)
            top = self._layout_top(h)
            if self.kicker:
                self._kicker(canvas, top, lt, out)
                top += self.kicker.cap + 34
            self.head.draw(canvas, MARGIN, top, lt, out, delay=0.10, stagger=0.08, dur=0.55)
            if self.sub:
                top += self.head.height + 60
                self.sub.draw(canvas, MARGIN, top, lt, out, delay=0.45, dur=0.5)
        elif self.kind == "stat":
            sub_h = (48 + self.sub.height) if self.sub else 0
            h = (self.kicker.cap + 40 if self.kicker else 0) + self.ncap + sub_h + (70 if self.source else 0)
            top = self._layout_top(h)
            if self.kicker:
                self._kicker(canvas, top, lt, out)
                top += self.kicker.cap + 40
            p = ease_out_expo((lt - 0.1) / 1.1)
            txt = self._fmt(self.value * p)
            pad = 40
            spr = shadowed((int(text_w(self.nf, self._fmt(self.value)) + 2 * pad + 20),
                            int(self.ncap + 2 * pad)),
                           [(pad, pad + self.ncap, txt, self.nf, ACCENT, 0)],
                           ((0, 10, 26, 0.5), (0, 3, 4, 0.3)))
            pin = ease_out_cubic((lt - 0.05) / 0.35)
            blit(canvas, spr, MARGIN - pad, top - pad + (1 - pin) * 30 - (1 - out) * 12, pin * out)
            top += self.ncap
            if self.sub:
                top += 48
                self.sub.draw(canvas, MARGIN, top, lt, out, delay=0.5, dur=0.5)
                top += self.sub.height
            if self.source:
                ps = ease_out_cubic((lt - 0.9) / 0.4) * out
                f = font(MONO_B, 24)
                s = ("SOURCE: " + self.source).upper()
                spr2 = shadowed((int(text_w(f, s, 2.4) + 40), 70), [(20, 46, s, f, (180, 184, 192), 2.4)],
                                ((0, 2, 6, 0.5),))
                blit(canvas, spr2, MARGIN - 20, top + 70 - 46, ps)
        elif self.kind == "end":
            ctaf = font(BOLD, 46)
            cta_h = 104
            h = (self.kicker.cap + 34 if self.kicker else 0) + self.head.height + 70 + cta_h + (
                64 if self.follow else 0)
            top = self._layout_top(h)
            if self.kicker:
                self._kicker(canvas, top, lt, out)
                top += self.kicker.cap + 34
            self.head.draw(canvas, MARGIN, top, lt, out, delay=0.08, stagger=0.08, dur=0.55)
            top += self.head.height + 70
            # CTA pill
            pc = ease_out_cubic((lt - 0.7) / 0.35) * out
            if pc > 0:
                tw_ = ctaf.getlength(self.cta)
                capc = cap_height(ctaf)
                bw, bh = tw_ + 76, cta_h
                pad = 30
                spr = Image.new("RGBA", (int(bw + 2 * pad), int(bh + 2 * pad)), (0, 0, 0, 0))
                sh = aa_rrect(spr.size, (pad, pad + 6, pad + bw, pad + bh + 6), bh / 2).filter(
                    ImageFilter.GaussianBlur(12)).point(lambda v: int(v * 0.45))
                shl = Image.new("RGBA", spr.size, (0, 0, 0, 0))
                shl.putalpha(sh)
                spr.alpha_composite(shl)
                pill = Image.new("RGBA", spr.size, ACCENT + (0,))
                pill.putalpha(aa_rrect(spr.size, (pad, pad, pad + bw, pad + bh), bh / 2))
                spr.alpha_composite(pill)
                draw_text(ImageDraw.Draw(spr), pad + 38, pad + bh / 2 + capc / 2, self.cta, ctaf, INK + (255,))
                s = lerp(0.92, 1.0, pc)
                if s < 0.999:
                    spr = spr.resize((int(spr.width * s), int(spr.height * s)), Image.LANCZOS)
                blit(canvas, spr, MARGIN - pad, top - pad + (1 - pc) * 14, pc)
            top += cta_h
            if self.follow:
                pf = ease_out_cubic((lt - 1.0) / 0.4) * out
                f = font(SEMI, 36)
                spr = shadowed((int(f.getlength(self.follow) + 40), 80),
                               [(20, 54, self.follow, f, SOFT, 0)], ((0, 3, 8, 0.5),))
                blit(canvas, spr, MARGIN - 20, top + 64 - 54 + 10, pf)

    def _kicker(self, canvas, top, lt, out):
        k = self.kicker
        pk = ease_out_cubic(lt / 0.35)
        blit(canvas, k.img, MARGIN - k.pad - (1 - pk) * 18, top - k.pad - (1 - out) * 12, pk * out)


# ------------------------------------------------------------------ media
def fetch(src, cache):
    if not re.match(r"https?://", src):
        return src
    os.makedirs(cache, exist_ok=True)
    ext = os.path.splitext(src.split("?")[0])[1][:5] or ".bin"
    path = os.path.join(cache, hashlib.sha1(src.encode()).hexdigest()[:16] + ext)
    if not os.path.exists(path):
        req = urllib.request.Request(src, headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64)"})
        with urllib.request.urlopen(req, timeout=300) as r, open(path + ".part", "wb") as fh:
            while True:
                b = r.read(1 << 20)
                if not b:
                    break
                fh.write(b)
        os.replace(path + ".part", path)
    return path


GRADE = "eq=contrast=1.05:saturation=1.06"


def decode(path, start, n, blur=False):
    vf = (f"scale={W}:{H}:force_original_aspect_ratio=increase:flags=lanczos,crop={W}:{H},"
          f"fps={FPS},{GRADE}")
    if blur:
        vf += ",gblur=sigma=36:steps=3,eq=brightness=-0.04:saturation=0.85"
    cmd = ["ffmpeg", "-v", "error", "-stream_loop", "-1", "-ss", f"{max(0.0, start):.3f}", "-i", path,
           "-frames:v", str(n), "-vf", vf, "-an", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"]
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, bufsize=W * H * 3)
    last = None
    got = 0
    while got < n:
        buf = p.stdout.read(W * H * 3)
        if len(buf) < W * H * 3:
            break
        last = Image.frombuffer("RGB", (W, H), buf, "raw", "RGB", 0, 1).copy()
        got += 1
        yield last
    p.stdout.close()
    p.wait()
    if last is None:
        last = Image.new("RGB", (W, H), (10, 10, 12))
    for _ in range(n - got):
        yield last


def kenburns(path, n, z0=1.0, z1=1.08, pan=(0.0, -0.015), blur=False):
    """Smooth sub-pixel push-in on a still image (zoom z0 -> z1, slight pan)."""
    img = Image.open(path).convert("RGB")
    s = max(W / img.width, H / img.height) * max(z0, z1) * 1.02   # never upscale past the source
    big = img.resize((max(W, int(img.width * s)), max(H, int(img.height * s))), Image.LANCZOS)
    if blur:
        big = big.filter(ImageFilter.GaussianBlur(36))
    cw = min(big.width, big.height * W / H)          # widest W:H window that fits
    for i in range(n):
        p = ease_in_out(i / max(n - 1, 1))
        z = lerp(z0, z1, p)
        ww = cw / z
        hh = ww * H / W
        mx, my = (big.width - ww) / 2, (big.height - hh) / 2
        cx = big.width / 2 + clamp(pan[0] * big.width * p, -mx, mx)
        cy = big.height / 2 + clamp(pan[1] * big.height * p, -my, my)
        yield big.transform((W, H), Image.EXTENT, (cx - ww / 2, cy - hh / 2, cx + ww / 2, cy + hh / 2),
                            Image.BICUBIC)


# ------------------------------------------------------------------ job
def _norm(w):
    return re.sub(r"[^\w'%-]", "", w.lower()).strip("-")


def build_tokens(job):
    """Words -> caption tokens. "display" edits rewrite words, by index {"i", "n"} or by text {"match"};
    "emphasis" lists word indexes or display texts shown in the accent colour."""
    words = [dict(w) for w in job["words"] if w.get("type", "word") == "word"]
    for i, w in enumerate(words):
        w["raw"] = w["text"]
        w["i"] = i
    normed = [_norm(w["text"]) for w in words]
    edits = []
    for e in job.get("display", []):
        e = dict(e)
        if "match" in e:
            target = [_norm(x) for x in e["match"].split()]
            hit = next((i for i in range(len(words) - len(target) + 1)
                        if normed[i:i + len(target)] == target), None)
            if hit is None:
                print(f"warning: display match not found: {e['match']!r}", file=sys.stderr)
                continue
            e["i"], e["n"] = hit, len(target)
        edits.append(e)
    edits.sort(key=lambda e: e["i"])
    em_idx = {x for x in job.get("emphasis", []) if isinstance(x, int)}
    em_txt = {_norm(x) for x in job.get("emphasis", []) if isinstance(x, str)}
    out, i = [], 0
    while i < len(words):
        e = next((e for e in edits if e["i"] == i), None)
        if e:
            n = int(e.get("n", 1))
            grp = words[i:i + n]
            out.append({"text": e["text"], "raw": grp[-1]["raw"], "start": grp[0]["start"], "end": grp[-1]["end"],
                        "em": bool(e.get("em")) or any(g["i"] in em_idx for g in grp)})
            i += n
        else:
            w = words[i]
            out.append({"text": w["text"], "raw": w["raw"], "start": w["start"], "end": w["end"],
                        "em": w["i"] in em_idx})
            i += 1
    for t in out:
        t["text"] = re.sub(r"[.,;:]+$", "", t["text"]).strip() or t["text"]
        if _norm(t["text"]) in em_txt:
            t["em"] = True
    return out


def mix_audio(job, cache, total, out):
    voice = fetch(job["voice"]["url"], cache)
    music = job.get("music")
    if music:
        mpath = fetch(music["url"], cache)
        gain = float(music.get("gain_db", -12))
        fc = (f"[0:a]aresample=48000,aformat=channel_layouts=stereo,apad=whole_dur={total},asplit=2[v1][v2];"
              f"[1:a]aresample=48000,aformat=channel_layouts=stereo,volume={gain}dB,afade=t=in:d=0.6,"
              f"apad=whole_dur={total}[m];"
              f"[m][v1]sidechaincompress=threshold=0.012:ratio=9:attack=25:release=450:makeup=1[md];"
              f"[v2][md]amix=inputs=2:normalize=0:duration=longest,atrim=0:{total},"
              f"afade=t=out:st={total - 1.0:.2f}:d=1.0,loudnorm=I=-14:TP=-1.5:LRA=11[out]")
        cmd = ["ffmpeg", "-y", "-v", "error", "-i", voice, "-stream_loop", "-1", "-i", mpath,
               "-filter_complex", fc, "-map", "[out]", "-t", f"{total:.3f}", "-ar", "48000", out]
    else:
        fc = (f"[0:a]aresample=48000,aformat=channel_layouts=stereo,apad=whole_dur={total},atrim=0:{total},"
              f"loudnorm=I=-14:TP=-1.5:LRA=11[out]")
        cmd = ["ffmpeg", "-y", "-v", "error", "-i", voice, "-filter_complex", fc, "-map", "[out]",
               "-t", f"{total:.3f}", "-ar", "48000", out]
    subprocess.run(cmd, check=True)


def probe_duration(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path],
                         capture_output=True, text=True, check=True).stdout.strip()
    return float(out)


def align_script(script, ww):
    """Give each script word the timing of the matching recognised word (spelling comes from the script)."""
    import difflib
    st = script.split()
    a = [_norm(x) for x in st]
    b = [_norm(x["text"]) for x in ww]
    times = [None] * len(st)
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(a=a, b=b, autojunk=False).get_opcodes():
        if tag == "equal":
            for k in range(i2 - i1):
                times[i1 + k] = (ww[j1 + k]["start"], ww[j1 + k]["end"])
        elif tag == "replace" and j2 > j1:
            s0, e0, n = ww[j1]["start"], ww[j2 - 1]["end"], i2 - i1
            for k in range(n):
                times[i1 + k] = (s0 + (e0 - s0) * k / n, s0 + (e0 - s0) * (k + 1) / n)
    i = 0
    while i < len(st):                       # fill runs of unmatched words
        if times[i] is not None:
            i += 1
            continue
        j = i
        while j < len(st) and times[j] is None:
            j += 1
        prev_end = times[i - 1][1] if i > 0 else 0.0
        next_start = times[j][0] if j < len(st) else prev_end + 0.35 * (j - i)
        # words after a sentence end inside the run belong to the next sentence (after the pause)
        m = next((k for k in range(j - 1, i - 1, -1) if k == 0 or re.search(r"[.?!]$", st[k - 1])), None)
        m = j if m is None else m
        est = {k: 0.07 * max(len(_norm(st[k])), 2) for k in range(i, j)}
        room = max(next_start - prev_end, 0.05 * (j - i))
        scale = min(1.0, room / sum(est.values()))
        t = prev_end
        for k in range(i, m):                                    # continue after the previous word
            times[k] = (t, t + est[k] * scale)
            t += est[k] * scale
        t = next_start - sum(est[k] * scale for k in range(m, j))
        for k in range(m, j):                                    # lead into the next recognised word
            times[k] = (t, t + est[k] * scale)
            t += est[k] * scale
        i = j
    matched = sum(1 for tag, i1, i2, *_ in difflib.SequenceMatcher(a=a, b=b, autojunk=False).get_opcodes()
                  if tag == "equal" for _ in range(i2 - i1))
    print(f"aligned {matched}/{len(st)} script words to the recognised words")
    return [{"text": t, "start": round(s0, 3), "end": round(e0, 3)} for t, (s0, e0) in zip(st, times)]


def ensure_words(job, cache, outdir):
    """Use job["words"] if given; otherwise time the script with Whisper (free, runs on the GitHub runner)."""
    if job.get("words"):
        return
    from faster_whisper import WhisperModel
    voice = fetch(job["voice"]["url"], cache)
    name = os.environ.get("WHISPER_MODEL", "small.en")
    model = WhisperModel(name, device="cpu", compute_type="int8")
    script = job.get("script", "")
    segs, _ = model.transcribe(voice, language="en", word_timestamps=True, beam_size=5,
                               initial_prompt=script[:220] or None, condition_on_previous_text=False)
    ww = [{"text": w.word.strip(), "start": float(w.start), "end": float(w.end)}
          for seg in segs for w in (seg.words or []) if w.word.strip()]
    print(f"whisper {name}: {len(ww)} words")
    job["words"] = align_script(script, ww) if script else ww
    with open(os.path.join(outdir, "words.json"), "w") as fh:
        json.dump(job["words"], fh, ensure_ascii=False)


def _find(normed, anchor, start_idx=0):
    target = [_norm(x) for x in anchor.split()]
    for i in range(start_idx, len(normed) - len(target) + 1):
        if normed[i:i + len(target)] == target:
            return i, i + len(target) - 1
    for i in range(0, len(normed) - len(target) + 1):          # fall back to any occurrence
        if normed[i:i + len(target)] == target:
            return i, i + len(target) - 1
    raise SystemExit(f"anchor not found in the voiceover: {anchor!r}")


def resolve_times(job, cache):
    """Turn word anchors ("at"/"until") into seconds so scenes cut exactly between sentences."""
    words = [w for w in job["words"] if w.get("type", "word") == "word"]
    normed = [_norm(w["text"]) for w in words]
    if not job.get("duration"):
        job["duration"] = round(probe_duration(fetch(job["voice"]["url"], cache)) + float(job.get("tail", 0.8)), 2)

    def cut(i):
        if i == 0:
            return 0.0
        gap = words[i]["start"] - words[i - 1]["end"]
        return max(0.0, words[i]["start"] - min(0.15, max(gap, 0.0) * 0.5))

    scenes, idx = job["scenes"], 0
    for k, s in enumerate(scenes):
        if "at" in s:
            i, _ = _find(normed, s["at"], idx)
            idx = i + 1
            s["start"] = 0.0 if k == 0 else round(cut(i), 3)
        elif k == 0:
            s["start"] = 0.0
    for k, s in enumerate(scenes):
        s["end"] = scenes[k + 1]["start"] if k + 1 < len(scenes) else job["duration"]
    idx = 0
    for t in job.get("titles", []):
        if "at" in t:
            i, _ = _find(normed, t["at"], idx)
            idx = i + 1
            t["start"] = round(cut(i) + 0.05, 3)
        elif "start" not in t:
            t["start"] = 0.0
        if "until" in t:
            _, j = _find(normed, t["until"], 0)
            t["end"] = round(words[j]["end"] + 0.25, 3)
        elif "end" not in t:
            t["end"] = t["start"] + float(t.get("dur", 3.3))
        host = next((s for s in scenes if s["start"] <= t["start"] < s["end"]), None)
        if host:
            t["end"] = round(min(t["end"], host["end"] - 0.05), 3)


def plan(job, cache):
    scenes = sorted(job["scenes"], key=lambda s: s["start"])
    total = float(job.get("duration") or scenes[-1]["end"])
    prev = None
    for s in scenes:
        s["n"] = int(round(s["end"] * FPS)) - int(round(s["start"] * FPS))
        s["f0"] = int(round(s["start"] * FPS))
        if s["type"] in ("video", "photo"):
            s["path"] = fetch(s["src"], cache)
            s["in"] = float(s.get("in", 0.0))
            prev = s
        elif s["type"] == "card":
            bg = s.get("bg", "prev")
            if bg == "prev" and prev is not None:
                s["bg_path"], s["bg_type"] = prev["path"], prev["type"]
                s["bg_in"] = prev["in"] + (prev["end"] - prev["start"]) if prev["type"] == "video" else 0
            elif isinstance(bg, dict):
                s["bg_path"] = fetch(bg["src"], cache)
                s["bg_type"] = bg.get("type", "video")
                s["bg_in"] = float(bg.get("in", 0))
            else:
                s["bg_path"] = None
            s["obj"] = Card(s)
    return scenes, total


def scene_frames(s, start_frame=0, count=None):
    n = s["n"] - start_frame if count is None else count
    off = start_frame / FPS
    if s["type"] == "video":
        return decode(s["path"], s["in"] + off, n)
    if s["type"] == "photo":
        return itertools.islice(kenburns(s["path"], s["n"], *s.get("zoom", (1.0, 1.08))), start_frame,
                                start_frame + n)
    if s.get("bg_path"):
        if s["bg_type"] == "photo":
            return itertools.islice(kenburns(s["bg_path"], s["n"], 1.04, 1.10, blur=True), start_frame,
                                    start_frame + n)
        return decode(s["bg_path"], s["bg_in"] + off, n, blur=True)
    return iter([Image.new("RGB", (W, H), (12, 13, 16))] * n)


def compose(job, scenes, s, base, t, captions, titles, xfade_from=None, j=0):
    global CARD_SHADE
    if s["type"] == "card":
        if xfade_from is not None and j < 8:
            base = Image.blend(xfade_from, base, ease_in_out((j + 1) / 8))
        canvas = base.convert("RGBA")
        if CARD_SHADE is None:
            CARD_SHADE = card_shade()
        a = ease_out_cubic((j + 1) / 8) if xfade_from is not None else 1.0
        blit(canvas, CARD_SHADE, 0, 0, a)
        s["obj"].draw(canvas, t - s["start"], s["end"] - s["start"])
    else:
        canvas = base.convert("RGBA")
        blit(canvas, BOTTOM_SCRIM, 0, H - BOTTOM_SCRIM.height)
    for ti in titles:
        ti.draw(canvas, t)
    captions.draw(canvas, t)
    return canvas.convert("RGB")


def render(job_path, out, stills=None):
    job = json.load(open(job_path))
    outdir = out if stills else os.path.dirname(os.path.abspath(out))
    os.makedirs(outdir, exist_ok=True)
    cache = os.path.join(outdir, ".cache")
    ensure_words(job, cache, outdir)
    resolve_times(job, cache)
    scenes, total = plan(job, cache)
    titles = [Title(t) for t in job.get("titles", [])]
    hide = [(t.t0, t.t1) for t in titles if t.hook]
    hide += [(s["start"], s["end"]) for s in scenes if s["type"] == "card"]
    hide += [tuple(h) for h in job.get("captions", {}).get("hide", [])]
    captions = Captions(build_tokens(job), hide)

    if stills:
        for t in stills:
            s = next(x for x in scenes if x["start"] <= t < x["end"])
            j = int(round(t * FPS)) - s["f0"]
            base = next(iter(scene_frames(s, j, 1)))
            compose(job, scenes, s, base, t, captions, titles, j=max(j, 8)).save(
                os.path.join(out, f"still_{t:06.2f}.png"))
        return

    audio = os.path.join(outdir, ".audio.wav")
    mix_audio(job, cache, total, audio)
    enc = subprocess.Popen(
        ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
         "-i", "-", "-i", audio, "-map", "0:v", "-map", "1:a",
         "-vf", "scale=out_color_matrix=bt709:out_range=tv,format=yuv420p",
         "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-profile:v", "high", "-level", "4.2",
         "-g", "60", "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709",
         "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-t", f"{total:.3f}", out],
        stdin=subprocess.PIPE)
    last = None
    written = 0
    N = int(round(total * FPS))
    for s in scenes:
        xf = last if (s["type"] == "card" and last is not None) else None
        for j, base in enumerate(scene_frames(s)):
            t = (s["f0"] + j) / FPS
            frame = compose(job, scenes, s, base, t, captions, titles, xfade_from=xf, j=j)
            enc.stdin.write(frame.tobytes())
            written += 1
            last = frame
            if written % 150 == 0:
                print(f"  {written}/{N} frames", flush=True)
    while written < N and last is not None:
        enc.stdin.write(last.tobytes())
        written += 1
    enc.stdin.close()
    if enc.wait() != 0:
        sys.exit("encoder failed")
    print(f"wrote {out} ({written} frames, {total:.2f}s)")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("job")
    ap.add_argument("out")
    ap.add_argument("--stills", help="comma-separated times; writes PNGs into OUT (a directory)")
    a = ap.parse_args()
    render(a.job, a.out, [float(x) for x in a.stills.split(",")] if a.stills else None)
