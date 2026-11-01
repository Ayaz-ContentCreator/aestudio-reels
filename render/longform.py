#!/usr/bin/env python3
"""AE Studio long-form renderer (YouTube, 1920x1080 / 30 fps) in the same design language as render/reel.py
(Inter Display + JetBrains Mono, accent #FFD23F, left-aligned editorial titles, word-highlight captions).

    python3 render/longform.py PLAN.json --slice 3 OUT.mp4        # one slice (video only) for the matrix render
    python3 render/longform.py PLAN.json --stills 1.0,64.2 OUTDIR  # QA stills (PNG)
    python3 render/longform.py PLAN.json --thumb OUT.jpg           # 1280x720 thumbnail

PLAN.json is written by tools/longform_prep.py (scenes with seconds, caption words, media paths, slices).
reel.py is imported and re-dimensioned for landscape; it is not modified.
"""
import argparse
import json
import math
import os
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import reel as R  # noqa: E402

W, H, FPS = 1920, 1080, 30
R.W, R.H, R.FPS = W, H, FPS
R.MARGIN = 150
R.TITLE_TOP = 124
R.CAP_BASE = 972
R.CAP_SIZE = 50
R.CAP_MAXW = 1380
R.LABEL_SIZE = 66
R.HOOK_SIZE = 96
R.BAND_Y = 540
R.TOP_SCRIM = R.vgrad(500, 0.74, 0.0, power=1.5)
R.BOTTOM_SCRIM = R.vgrad(430, 0.0, 0.64, power=1.5)
M = R.MARGIN
ACCENT, WHITE, SOFT, INK = R.ACCENT, R.WHITE, R.SOFT, R.INK
font, blit, shadowed, TextBlock, Kicker = R.font, R.blit, R.shadowed, R.TextBlock, R.Kicker
eo, ex, eio, clamp, lerp = R.ease_out_cubic, R.ease_out_expo, R.ease_in_out, R.clamp, R.lerp
BLACK, XBOLD, BOLD, SEMI, MONO, MONO_B = R.BLACK, R.XBOLD, R.BOLD, R.SEMI, R.MONO, R.MONO_B
CAPTION_TYPES = {"photo", "video", "map", "timeline"}


# ------------------------------------------------------------------ captions (landscape: up to 6 words)
class Captions(R.Captions):
    def _cost(self, seg, a, b):
        g = seg[a:b]
        if len(g) > 6 or R.text_w(self.f, " ".join(w["text"] for w in g)) > R.CAP_MAXW:
            return None
        d = g[-1]["end"] - g[0]["start"]
        c = 1.0 + max(0.0, 0.8 - d) * 3 + max(0.0, d - 2.6) * 2
        if len(g) == 1 and len(seg) > 1:
            c += 1.4
        if b < len(seg):
            last, nxt = g[-1]["text"], seg[b]["text"]
            if R._bare(last) in R.FUNC:
                c += 2.0
            if last[:1].isupper() and nxt[:1].isupper():
                c += 2.5
                if not (seg[b + 1]["text"][:1].isupper() if b + 1 < len(seg) else False):
                    c += 1.5
        return c

    def _segment(self, seg):
        n = len(seg)
        best = [0.0] + [math.inf] * n
        back = [0] * (n + 1)
        for i in range(1, n + 1):
            for j in range(max(0, i - 6), i):
                c = self._cost(seg, j, i)
                if c is not None and best[j] + c < best[i]:
                    best[i], back[i] = best[j] + c, j
            if best[i] == math.inf:
                best[i], back[i] = best[i - 1] + 1, i - 1
        out, i = [], n
        while i > 0:
            out.append(seg[back[i]:i])
            i = back[i]
        return out[::-1]


# ------------------------------------------------------------------ backgrounds
class Studio:
    """Dark charcoal stage: soft key light, slow drifting accent glow, faint 'ring rope' lines, film grain."""

    def __init__(self):
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        r = np.sqrt(((xx - W * 0.28) / (W * 0.95)) ** 2 + ((yy - H * 0.22) / (H * 1.15)) ** 2)
        lum = 11.0 + 17.0 * np.clip(1 - r, 0, 1) ** 1.7
        vig = np.clip(np.sqrt(((xx - W / 2) / (W * 0.62)) ** 2 + ((yy - H / 2) / (H * 0.62)) ** 2), 0, 1.4)
        lum *= 1 - 0.35 * np.clip(vig - 0.55, 0, 1)
        base = np.stack([lum * 0.97, lum * 1.0, lum * 1.09], -1)
        for k, y in enumerate((0.80, 0.86, 0.92)):                     # three faint rope lines
            yi = int(H * y)
            base[yi:yi + 2, :, :] += 6.5 - k * 1.5
        self.base = base.astype(np.float32)
        g = np.mgrid[0:900, 0:900].astype(np.float32)
        d = np.sqrt((g[0] - 450) ** 2 + (g[1] - 450) ** 2) / 450
        blob = np.clip(1 - d, 0, 1) ** 2.2 * 16.0
        self.glow = np.stack([blob * 1.0, blob * 0.82, blob * 0.25], -1).astype(np.float32)
        rng = np.random.default_rng(11)
        self.grain = [rng.normal(0, 2.6, (H, W, 1)).astype(np.float32) for _ in range(4)]

    def frame(self, t, accent=True):
        f = self.base.copy()
        if accent:
            gx = int(W * (0.74 + 0.06 * math.sin(t * 0.11)) - 450)
            gy = int(H * (0.30 + 0.08 * math.cos(t * 0.09)) - 450)
            x0, y0, x1, y1 = max(gx, 0), max(gy, 0), min(gx + 900, W), min(gy + 900, H)
            if x1 > x0 and y1 > y0:
                f[y0:y1, x0:x1] += self.glow[y0 - gy:y1 - gy, x0 - gx:x1 - gx]
        f += self.grain[int(t * FPS) % 4]
        return Image.fromarray(np.clip(f, 0, 255).astype(np.uint8), "RGB")


STUDIO = None


def studio(t, accent=True):
    global STUDIO
    if STUDIO is None:
        STUDIO = Studio()
    return STUDIO.frame(t, accent)


class BlurBG:
    """A photo/video still as a blurred, darkened, slowly drifting card background."""

    def __init__(self, path):
        img = Image.open(path).convert("RGB")
        s = max(W * 1.14 / img.width, H * 1.14 / img.height) / 2
        small = img.resize((max(2, int(img.width * s)), max(2, int(img.height * s))), Image.BILINEAR)
        small = small.filter(ImageFilter.GaussianBlur(10))
        small = Image.eval(small, lambda v: int(v * 0.58))
        self.img = small.resize((small.width * 2, small.height * 2), Image.BILINEAR)
        self.shade = R.card_shade()

    def frame(self, lt, dur):
        p = eio(lt / max(dur, 0.1))
        mx, my = self.img.width - W, self.img.height - H
        x, y = int(mx * lerp(0.35, 0.65, p)), int(my * lerp(0.6, 0.4, p))
        c = self.img.crop((x, y, x + W, y + H)).convert("RGBA")
        c.alpha_composite(self.shade)
        return c


def video_still(path, at):
    out = path + f".still{at:.1f}.jpg"
    if not os.path.exists(out):
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{at:.2f}", "-i", path, "-frames:v", "1", "-q:v", "3",
                        out], check=True)
    return out


# ------------------------------------------------------------------ small drawing helpers
def text_sprite(s, fname, size, rgb, tr=0.0, shadow=((0, 4, 12, 0.5), (0, 2, 3, 0.3))):
    f = font(fname, size)
    cap = R.cap_height(f)
    pad = 30
    spr = shadowed((int(R.text_w(f, s, tr) + 2 * pad), int(cap + 2 * pad + size * 0.3)),
                   [(pad, pad + cap, s, f, rgb, tr)], shadow)
    return spr, pad, cap


def kicker_draw(canvas, k, x, top, lt, out, delay=0.0):
    pk = eo((lt - delay) / 0.35)
    blit(canvas, k.img, x - k.pad - (1 - pk) * 18, top - k.pad - (1 - out) * 10, pk * out)


def credit_draw(canvas, text, lt, dur):
    if not text:
        return
    s = str(text).upper()
    f = font(MONO_B, 19)
    tr = 1.8
    cap = R.cap_height(f)
    pad = 18
    spr = shadowed((int(R.text_w(f, s, tr) + 2 * pad), int(cap + 2 * pad + 6)),
                   [(pad, pad + cap, s, f, (232, 234, 238), tr)], ((0, 2, 6, 0.8), (0, 1, 2, 0.6)))
    op = eo(lt / 0.3) * eo((dur - lt) / 0.2) * 0.85
    blit(canvas, spr, W - M + 40 - spr.width + pad, 52 - pad, op)


def pill(text, size=44, bg=ACCENT, fg=INK):
    f = font(BOLD, size)
    cap = R.cap_height(f)
    tw = f.getlength(text)
    bw, bh = tw + 80, int(size * 2.15)
    pad = 30
    spr = Image.new("RGBA", (int(bw + 2 * pad), int(bh + 2 * pad)), (0, 0, 0, 0))
    sh = R.aa_rrect(spr.size, (pad, pad + 6, pad + bw, pad + bh + 6), bh / 2).filter(
        ImageFilter.GaussianBlur(12)).point(lambda v: int(v * 0.45))
    shl = Image.new("RGBA", spr.size, (0, 0, 0, 0))
    shl.putalpha(sh)
    spr.alpha_composite(shl)
    p = Image.new("RGBA", spr.size, bg + (0,))
    p.putalpha(R.aa_rrect(spr.size, (pad, pad, pad + bw, pad + bh), bh / 2))
    spr.alpha_composite(p)
    R.draw_text(ImageDraw.Draw(spr), pad + 40, pad + bh / 2 + cap / 2, text, f, fg + (255,))
    return spr, pad, bh


def rgba_line(canvas, pts, rgb, width, op=1.0):
    layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    ImageDraw.Draw(layer).line(pts, fill=rgb + (int(255 * op),), width=width, joint="curve")
    canvas.alpha_composite(layer)


# ------------------------------------------------------------------ cards
class Card:
    """Full-frame typography over the studio (or a blurred photo)."""

    def __init__(self, s):
        self.s = s
        self.kind = s["type"]
        k = self.kind
        self.kicker = Kicker(s["kicker"], 32) if s.get("kicker") else None
        if k == "chapter":
            self.title = TextBlock(s["title"], BLACK, 128, 1250, max_lines=2, leading=1.0)
            self.kicker = Kicker(f"Chapter {s['num']:02d} · {s.get('kicker', '')}".strip(" ·"), 32)
            f = font(BLACK, 600)
            num = f"{s['num']:02d}"
            nw = int(f.getlength(num)) + 40
            img = Image.new("RGBA", (nw, 700), (0, 0, 0, 0))
            ImageDraw.Draw(img).text((20, 600), num, font=f, anchor="ls", fill=(0, 0, 0, 0),
                                     stroke_width=3, stroke_fill=ACCENT + (255,))
            self.num = img
        elif k == "title":
            self.title = TextBlock(s["text"], BLACK, 250, W - 2 * M, max_lines=1, leading=1.0)
            self.sub = text_sprite(s.get("sub", ""), MONO, 40, SOFT, tr=4)
        elif k == "statement":
            self.head = TextBlock(s["text"], BLACK, s.get("size", 108), 1500, max_lines=3, leading=1.02)
        elif k == "headline":
            self.head = TextBlock(s["text"], BLACK, s.get("size", 100), 1480, max_lines=3, leading=1.02)
            self.sub = TextBlock(s["sub"], SEMI, 46, 1400, max_lines=2, color=SOFT) if s.get("sub") else None
        elif k == "stat":
            self.value = float(s["value"])
            self.dec = int(s.get("decimals", 0))
            self.pre, self.suf = s.get("prefix", ""), s.get("suffix", "")
            final = self._fmt(self.value)
            self.nsize = R.fit_size(BLACK, final, 1500, 320, 120)
            self.nf = font(BLACK, self.nsize)
            self.ncap = R.cap_height(self.nf)
            self.sub = TextBlock(s["sub"], BOLD, 54, 1400, max_lines=2) if s.get("sub") else None
            self.source = text_sprite("SOURCE: " + s["source"], MONO_B, 24, (180, 184, 192), tr=2.4,
                                      shadow=((0, 2, 6, 0.5),)) if s.get("source") else None
        elif k == "quote":
            self.mark = text_sprite("“", BLACK, 300, ACCENT, shadow=((0, 6, 18, 0.4),))
            self.head = TextBlock(s["text"], BOLD, 82, 1450, max_lines=3, leading=1.08)
            self.by = text_sprite("— " + s["by"], MONO_B, 28, SOFT, tr=2.2) if s.get("by") else None
        elif k == "list":
            self.title = TextBlock(s["title"], BLACK, 84, 1450, max_lines=1) if s.get("title") else None
            n = len(s["items"])
            size = 58 if n <= 4 else 52
            self.items = [text_sprite(it, BOLD, size, WHITE) for it in s["items"]]
            self.isize = size
        elif k == "versus":
            ls = R.fit_size(BLACK, s["left"].upper(), 720, 104, 56)
            rs = R.fit_size(BLACK, s["right"].upper(), 720, 104, 56)
            sz = min(ls, rs)
            self.left = text_sprite(s["left"].upper(), BLACK, sz, WHITE)
            self.right = text_sprite(s["right"].upper(), BLACK, sz, WHITE)
            self.vs = text_sprite("VS", MONO, 54, ACCENT, tr=6)
            self.sub = TextBlock(s["sub"], SEMI, 46, 1500, max_lines=2, color=SOFT) if s.get("sub") else None
        elif k == "bars":
            self.title = TextBlock(s["title"], BLACK, 84, 1450, max_lines=1) if s.get("title") else None
            self.rows = [(text_sprite(lbl, BOLD, 42, SOFT), float(v), text_sprite(vt, BLACK, 56, WHITE))
                         for lbl, v, vt in s["items"]]
            self.vmax = max(v for _, v, _ in self.rows)
        elif k == "end":
            self.head = TextBlock(s["text"], BLACK, s.get("size", 110), 1100, max_lines=3, leading=1.0)
            self.cta = pill(s.get("cta", "Subscribe"))
            self.follow = text_sprite(s["follow"], SEMI, 38, SOFT) if s.get("follow") else None
        elif k == "timeline":
            self.label = text_sprite(s["label"], BLACK, 70, WHITE)
        self.bg = BlurBG(s["bg_path"]) if s.get("bg_path") else None

    def _fmt(self, v):
        s = f"{v:,.{self.dec}f}"
        return f"{self.pre}{s}{self.suf}"

    def background(self, t, lt, dur):
        if self.bg:
            return self.bg.frame(lt, dur)
        return studio(t, accent=self.kind != "end").convert("RGBA")

    def draw(self, canvas, lt, dur):
        out = eo((dur - lt) / 0.22)
        k = self.kind
        if k == "chapter":
            p = clamp(lt / 0.32)
            if p < 1:                                     # accent wipe in
                x1 = W * ex(p) * 1.3
                ImageDraw.Draw(canvas).rectangle((x1 - W * 0.35, 0, x1, H), fill=ACCENT + (255,))
            pn = eo((lt - 0.15) / 0.9)
            blit(canvas, self.num, W - M - self.num.width + 60 + (1 - pn) * 80, H / 2 - 420, 0.22 * pn * out)
            top = int(H * 0.40)
            kicker_draw(canvas, self.kicker, M, top, lt - 0.18, out)
            top += self.kicker.cap + 36
            self.title.draw(canvas, M, top, lt, out, delay=0.30, stagger=0.09, dur=0.6)
            bar = ex((lt - 0.55) / 0.7)
            y = top + self.title.height + 46
            ImageDraw.Draw(canvas).rectangle((M, y, M + 260 * bar, y + 7), fill=ACCENT + (int(255 * out),))
        elif k == "title":
            top = int(H * 0.36)
            kicker_draw(canvas, self.kicker, M, top, lt, out) if self.kicker else None
            top += (self.kicker.cap + 40) if self.kicker else 0
            self.title.draw(canvas, M, top, lt, out, delay=0.1, dur=0.8)
            spr, pad, cap = self.sub
            ps = eo((lt - 0.7) / 0.5) * out
            blit(canvas, spr, M - pad, top + self.title.height + 70 - pad, ps)
        elif k == "statement":
            h = (self.kicker.cap + 36 if self.kicker else 0) + self.head.height
            top = int(H * 0.47 - h / 2)
            if self.kicker:
                kicker_draw(canvas, self.kicker, M, top, lt, out)
                top += self.kicker.cap + 36
            self.head.draw(canvas, M, top, lt, out, delay=0.08, stagger=0.08, dur=0.55)
        elif k == "headline":
            h = (self.kicker.cap + 36 if self.kicker else 0) + self.head.height + (
                56 + self.sub.height if self.sub else 0)
            top = int(H * 0.47 - h / 2)
            if self.kicker:
                kicker_draw(canvas, self.kicker, M, top, lt, out)
                top += self.kicker.cap + 36
            self.head.draw(canvas, M, top, lt, out, delay=0.10, stagger=0.08, dur=0.55)
            if self.sub:
                top += self.head.height + 56
                self.sub.draw(canvas, M, top, lt, out, delay=0.45, dur=0.5)
        elif k == "stat":
            sub_h = (50 + self.sub.height) if self.sub else 0
            h = (self.kicker.cap + 44 if self.kicker else 0) + self.ncap + sub_h + (70 if self.source else 0)
            top = int(H * 0.47 - h / 2)
            if self.kicker:
                kicker_draw(canvas, self.kicker, M, top, lt, out)
                top += self.kicker.cap + 44
            p = ex((lt - 0.1) / 1.2)
            txt = self._fmt(self.value * p)
            pad = 44
            spr = shadowed((int(R.text_w(self.nf, self._fmt(self.value)) + 2 * pad + 30), int(self.ncap + 2 * pad)),
                           [(pad, pad + self.ncap, txt, self.nf, ACCENT, 0)], ((0, 10, 26, 0.5), (0, 3, 4, 0.3)))
            pin = eo((lt - 0.05) / 0.35)
            blit(canvas, spr, M - pad, top - pad + (1 - pin) * 30 - (1 - out) * 12, pin * out)
            top += self.ncap
            if self.sub:
                top += 50
                self.sub.draw(canvas, M, top, lt, out, delay=0.5, dur=0.5)
                top += self.sub.height
            if self.source:
                s2, pad2, cap2 = self.source
                blit(canvas, s2, M - pad2, top + 64 - pad2 - cap2, eo((lt - 0.9) / 0.4) * out)
        elif k == "quote":
            mspr, mpad, mcap = self.mark
            h = self.head.height + (90 if self.by else 0)
            top = int(H * 0.50 - h / 2)
            blit(canvas, mspr, M - mpad - 14, top - mcap - 30 - mpad + 150, eo(lt / 0.4) * out * 0.95)
            self.head.draw(canvas, M, top + 40, lt, out, delay=0.15, stagger=0.09, dur=0.6)
            if self.by:
                s2, pad2, cap2 = self.by
                blit(canvas, s2, M - pad2, top + 40 + self.head.height + 86 - pad2 - cap2, eo((lt - 0.7) / 0.4) * out)
        elif k == "list":
            n = len(self.items)
            pitch = int(self.isize * 1.62)
            h = (self.kicker.cap + 40 if self.kicker else 0) + (self.title.height + 60 if self.title else 0) + pitch * n
            top = int(H * 0.47 - h / 2)
            if self.kicker:
                kicker_draw(canvas, self.kicker, M, top, lt, out)
                top += self.kicker.cap + 40
            if self.title:
                self.title.draw(canvas, M, top, lt, out, delay=0.1)
                top += self.title.height + 60
            step = min(0.55, max(0.18, (dur * 0.55) / max(n, 1)))
            d = ImageDraw.Draw(canvas)
            for i, (spr, pad, cap) in enumerate(self.items):
                p = eo((lt - 0.25 - i * step) / 0.35) * out
                if p <= 0:
                    continue
                y = top + i * pitch
                sq = int(self.isize * 0.30)
                d.rectangle((M, y + cap / 2 - sq / 2 + 2, M + sq, y + cap / 2 + sq / 2 + 2),
                            fill=ACCENT + (int(255 * p),))
                blit(canvas, spr, M + sq + 30 - pad + (1 - p) * 24, y - pad, p)
        elif k == "versus":
            top = int(H * 0.30)
            if self.kicker:
                kicker_draw(canvas, self.kicker, M, top, lt, out)
            cy = int(H * 0.52)
            (ls, lpad, lcap), (rs, rpad, rcap), (vsp, vpad, vcap) = self.left, self.right, self.vs
            pl, pr = ex((lt - 0.1) / 0.6), ex((lt - 0.22) / 0.6)
            blit(canvas, ls, M - lpad - (1 - pl) * 60, cy - lcap / 2 - lpad, pl * out)
            blit(canvas, rs, W - M - rs.width + rpad + (1 - pr) * 60, cy - rcap / 2 - rpad, pr * out)
            pv = eo((lt - 0.35) / 0.4) * out
            blit(canvas, vsp, W / 2 - vsp.width / 2, cy - vcap / 2 - vpad, pv)
            ln = ex((lt - 0.3) / 0.6)
            ImageDraw.Draw(canvas).rectangle((M, cy + lcap / 2 + 44, M + (W - 2 * M) * ln, cy + lcap / 2 + 48),
                                             fill=ACCENT + (int(200 * out),))
            if self.sub:
                self.sub.draw(canvas, M, cy + lcap / 2 + 110, lt, out, delay=0.6, dur=0.5)
        elif k == "bars":
            top = int(H * 0.26)
            if self.kicker:
                kicker_draw(canvas, self.kicker, M, top, lt, out)
                top += self.kicker.cap + 40
            if self.title:
                self.title.draw(canvas, M, top, lt, out, delay=0.1)
                top += self.title.height + 80
            maxw = W - 2 * M - 300
            d = ImageDraw.Draw(canvas)
            for i, ((lspr, lpad, lcap), v, (vspr, vpad, vcap)) in enumerate(self.rows):
                y = top + i * 170
                pl = eo((lt - 0.3 - i * 0.3) / 0.35) * out
                blit(canvas, lspr, M - lpad, y - lpad, pl)
                pb = ex((lt - 0.45 - i * 0.3) / 1.0)
                bw = max(8, maxw * (v / self.vmax) * pb)
                col = ACCENT if i == 0 else (236, 238, 242)
                by = y + lcap + 26
                bar = R.aa_rrect(canvas.size, (M, by, M + bw, by + 52), 10)
                lay = Image.new("RGBA", canvas.size, col + (0,))
                lay.putalpha(bar.point(lambda a, o=out: int(a * o)))
                canvas.alpha_composite(lay)
                blit(canvas, vspr, M + bw + 28 - vpad, by + 26 - vcap / 2 - vpad, eo((lt - 0.9 - i * 0.3) / 0.4) * out)
        elif k == "end":
            ctaspr, cpad, cbh = self.cta
            h = (self.kicker.cap + 36 if self.kicker else 0) + self.head.height + 70 + cbh + (70 if self.follow else 0)
            top = int(H * 0.47 - h / 2)
            if self.kicker:
                kicker_draw(canvas, self.kicker, M, top, lt, out)
                top += self.kicker.cap + 36
            self.head.draw(canvas, M, top, lt, out, delay=0.08, stagger=0.08, dur=0.55)
            top += self.head.height + 70
            pc = eo((lt - 0.7) / 0.35) * out
            blit(canvas, ctaspr, M - cpad, top - cpad + (1 - pc) * 14, pc)
            top += cbh
            if self.follow:
                fs, fpad, fcap = self.follow
                blit(canvas, fs, M - fpad, top + 64 - fpad - fcap, eo((lt - 1.0) / 0.4) * out)
        elif k == "timeline":
            self._timeline(canvas, lt, dur, out)

    def _timeline(self, canvas, lt, dur, out):
        s = self.s
        a, z = (float(x) for x in s["axis"])
        x0, x1 = M + 20, W - M - 20
        y = int(H * 0.62)

        def X(v):
            return x0 + (x1 - x0) * (v - a) / max(z - a, 1e-6)

        top = int(H * 0.24)
        if self.kicker:
            kicker_draw(canvas, self.kicker, M, top, lt, out)
        p = eio((lt - 0.2) / max(0.8, dur * 0.55))
        cur = lerp(float(s["from"]), float(s["to"]), p)
        d = ImageDraw.Draw(canvas)
        pa = eo(lt / 0.4) * out
        d.rectangle((x0, y - 2, x1, y + 2), fill=(200, 204, 212, int(90 * pa)))
        d.rectangle((x0, y - 4, X(cur), y + 4), fill=ACCENT + (int(255 * pa),))
        span = int(z - a)
        step = 1 if span <= 12 else (2 if span <= 24 else 5)
        f = font(MONO_B, 28)
        for yr in range(int(math.ceil(a)), int(z) + 1):
            if (yr - int(math.ceil(a))) % step:
                continue
            xx = X(yr)
            near = abs(yr - cur) < 0.5
            col = ACCENT if near else (190, 194, 202)
            d.rectangle((xx - 1, y - 14, xx + 1, y + 14), fill=col + (int(255 * pa),))
            d.text((xx, y + 56), str(yr), font=f, anchor="ms", fill=col + (int(255 * pa),))
        cx = X(cur)
        r = 15
        d.ellipse((cx - r, y - r, cx + r, y + r), fill=ACCENT + (int(255 * pa),))
        d.ellipse((cx - r * 2.2, y - r * 2.2, cx + r * 2.2, y + r * 2.2), outline=ACCENT + (int(110 * pa),), width=3)
        spr, pad, cap = self.label
        lx = clamp(cx - (spr.width - 2 * pad) / 2, M, W - M - (spr.width - 2 * pad))
        pl = eo((lt - 0.6) / 0.4) * out
        blit(canvas, spr, lx - pad, y - 80 - cap - pad + (1 - pl) * 16, pl)


# ------------------------------------------------------------------ map
_MAPS = {}


def _project(view):
    lon0, lon1, lat0, lat1 = view
    k = math.cos(math.radians((lat0 + lat1) / 2))
    bw, bh = (lon1 - lon0) * k, (lat1 - lat0)
    s = min((W - 2 * 110) / bw, (H - 2 * 120) / bh)
    ox = (W - bw * s) / 2
    oy = (H - bh * s) / 2

    def P(lat, lon):
        return ox + (lon - lon0) * k * s, oy + (lat1 - lat) * s
    return P


def base_map(view, geo_dir):
    key = tuple(view)
    if key in _MAPS:
        return _MAPS[key]
    P = _project(view)
    ss = 2
    img = Image.new("RGBA", (W * ss, H * ss), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    def rings(geom):
        if geom["type"] == "Polygon":
            yield from geom["coordinates"]
        elif geom["type"] == "MultiPolygon":
            for poly in geom["coordinates"]:
                yield from poly
        elif geom["type"] == "LineString":
            yield geom["coordinates"]
        elif geom["type"] == "MultiLineString":
            yield from geom["coordinates"]

    def pts(ring):
        return [(P(lat, lon)[0] * ss, P(lat, lon)[1] * ss) for lon, lat in ring]
    land = json.load(open(os.path.join(geo_dir, "land.geojson")))
    for ft in land["features"]:
        for ring in rings(ft["geometry"]):
            if len(ring) > 2:
                d.polygon(pts(ring), fill=(38, 42, 51, 255), outline=(84, 90, 103, 255))
    for name, col, wd in (("borders.geojson", (88, 94, 106, 255), 2), ("states.geojson", (52, 57, 66, 255), 1)):
        p = os.path.join(geo_dir, name)
        if os.path.exists(p):
            for ft in json.load(open(p))["features"]:
                for ring in rings(ft["geometry"]):
                    d.line(pts(ring), fill=col, width=wd * ss)
    img = img.resize((W, H), Image.LANCZOS)
    _MAPS[key] = (img, P)
    return _MAPS[key]


class MapScene:
    def __init__(self, s, geo_dir):
        self.s = s
        self.img, self.P = base_map(s["view"], geo_dir)
        self.pts = [(name, self.P(lat, lon)) for name, lat, lon in s["points"]]
        self.labels = [text_sprite(n, BOLD, 38, WHITE) for n, _ in self.pts]
        self.kicker = Kicker(s["kicker"], 32) if s.get("kicker") else None

    def draw(self, canvas, t, lt, dur):
        base = studio(t, accent=False).convert("RGBA")
        canvas.paste(base)
        z = lerp(1.0, 1.04, eio(lt / max(dur, 0.1)))
        mp = self.img
        if z > 1.001:
            mw, mh = W / z, H / z
            mp = mp.transform((W, H), Image.EXTENT, ((W - mw) / 2, (H - mh) / 2, (W + mw) / 2, (H + mh) / 2),
                              Image.BICUBIC)
        canvas.alpha_composite(mp)

        def Z(pt):
            return (W / 2 + (pt[0] - W / 2) * z, H / 2 + (pt[1] - H / 2) * z)
        n = len(self.pts)
        t0 = 0.5
        seg = max(0.6, (dur * 0.82 - t0) / max(n - 1, 1))
        d = ImageDraw.Draw(canvas)
        path = [Z(self.pts[0][1])]
        for i in range(1, n):
            p = eio((lt - t0 - (i - 1) * seg) / (seg * 0.8))
            if p <= 0:
                break
            a, b = Z(self.pts[i - 1][1]), Z(self.pts[i][1])
            path.append((lerp(a[0], b[0], p), lerp(a[1], b[1], p)))
        if len(path) > 1:
            rgba_line(canvas, path, ACCENT, 6, 0.95)
        for i in range(n):
            appear = t0 + (i - 1) * seg + seg * 0.8 if i else 0.15
            p = eo((lt - appear) / 0.3)
            if p <= 0:
                continue
            x, y = Z(self.pts[i][1])
            r = 11 * p
            d.ellipse((x - r, y - r, x + r, y + r), fill=ACCENT + (255,))
            ring = (lt - appear) % 1.6 / 1.6
            rr = 12 + 26 * ring
            d.ellipse((x - rr, y - rr, x + rr, y + rr), outline=ACCENT + (int(160 * (1 - ring) * p),), width=3)
            spr, pad, cap = self.labels[i]
            lx = x + 22 if x < W - 360 else x - 22 - (spr.width - 2 * pad)
            blit(canvas, spr, lx - pad, y - cap / 2 - pad - 4, p)
        if self.kicker:
            blit(canvas, R.TOP_SCRIM, 0, 0, 0.6)
            kicker_draw(canvas, self.kicker, M, R.TITLE_TOP, lt, eo((dur - lt) / 0.22))


# ------------------------------------------------------------------ photo / video
class Label:
    """Kicker + headline over footage (top-left), like the Reel label titles."""

    def __init__(self, spec, maxw=W - 2 * M, size=None):
        self.kicker = Kicker(spec["kicker"], 30) if spec.get("kicker") else None
        self.block = TextBlock(spec["text"], BLACK, size or R.LABEL_SIZE, maxw, max_lines=2)

    def draw(self, canvas, lt, dur, x=M, top=None, scrim=True):
        out = eo((dur - lt) / 0.22)
        if scrim:
            blit(canvas, R.TOP_SCRIM, 0, 0, eo(lt / 0.3) * out)
        top = R.TITLE_TOP if top is None else top
        if self.kicker:
            kicker_draw(canvas, self.kicker, x, top, lt, out)
            top += self.kicker.cap + 28
        self.block.draw(canvas, x, top, lt, out, delay=0.06)


class Media:
    def __init__(self, s):
        self.s = s
        self.kind = s["type"]
        self.path = s["path"]
        self.credit = s.get("credit")
        if self.kind == "photo":
            img = Image.open(self.path)
            fit = s.get("fit")
            if not fit:
                fit = "frame" if min(img.width / W, img.height / H) < 0.72 else "fill"
            self.fit = fit
        else:
            self.fit = "fill"
        lab = s.get("label")
        if self.fit == "frame":
            img = Image.open(self.path).convert("RGB")
            sc = min(W * 0.50 / img.width, H * 0.64 / img.height)
            self.fw, self.fh = int(img.width * sc), int(img.height * sc)
            self.photo = img.resize((int(self.fw * 1.05) + 2, int(self.fh * 1.05) + 2), Image.LANCZOS)
            self.bg = BlurBG(self.path)
            sh = Image.new("L", (self.fw + 120, self.fh + 120), 0)
            ImageDraw.Draw(sh).rectangle((60, 72, 60 + self.fw, 72 + self.fh), fill=170)
            self.shadow = Image.new("RGBA", sh.size, (0, 0, 0, 0))
            self.shadow.putalpha(sh.filter(ImageFilter.GaussianBlur(26)))
            self.label = Label(lab, maxw=W - 2 * M - self.fw - 110, size=84) if lab else None
        else:
            self.label = Label(lab) if lab else None
        self.gen = None

    def frames(self, n):
        s = self.s
        if self.kind == "video" and s.get("fit") == "pillar":
            return decode_pillar(self.path, float(s.get("in", 0)), n)
        if self.kind == "video":
            return R.decode(self.path, float(s.get("in", 0)), n, fit="fill", focus=R._focus(s))
        if self.fit == "fill":
            z0, z1 = s.get("zoom", (1.0, 1.08))
            return R.kenburns(self.path, n, z0, z1, fit="fill", focus=R._focus(s))
        return None

    def draw_frame(self, base, canvas_t, lt, dur):
        if self.fit == "frame":
            c = self.bg.frame(lt, dur)
            p = eo(lt / 0.5)
            z = lerp(1.0, 1.05, eio(lt / max(dur, 0.1)))
            ww, hh = self.photo.width / z, self.photo.height / z
            cx, cy = self.photo.width / 2, self.photo.height / 2
            fg = self.photo.transform((self.fw, self.fh), Image.EXTENT,
                                      (cx - ww / 2, cy - hh / 2, cx + ww / 2, cy + hh / 2), Image.BICUBIC)
            x = W - M - self.fw if self.label else (W - self.fw) // 2
            y = int(H * 0.50 - self.fh / 2 + (1 - p) * 30)
            blit(c, self.shadow, x - 60, y - 60, p)
            c.alpha_composite(fg.convert("RGBA"), (x, y)) if p >= 0.999 else blit(c, fg.convert("RGBA"), x, y, p)
            if self.label:
                h = (self.label.kicker.cap + 28 if self.label.kicker else 0) + self.label.block.height
                self.label.draw(c, lt, dur, x=M, top=int(H * 0.47 - h / 2), scrim=False)
            return c
        c = base.convert("RGBA")
        blit(c, R.BOTTOM_SCRIM, 0, H - R.BOTTOM_SCRIM.height)
        if self.label:
            self.label.draw(c, lt, dur)
        return c


def decode_pillar(path, start, n):
    """Upright (portrait/square) video: whole frame, centred, over a blurred, darker fill of itself."""
    fh = int(H * 0.88) // 2 * 2
    vf = (f"fps={FPS},split[a][b];"
          f"[a]scale={W // 4}:{H // 4}:force_original_aspect_ratio=increase,crop={W // 4}:{H // 4},"
          f"gblur=sigma=10:steps=2,scale={W}:{H}:flags=bilinear,eq=brightness=-0.16:saturation=0.75[bg];"
          f"[b]scale=-2:{fh}:flags=lanczos[fg];[bg][fg]overlay=x=(W-w)/2:y=(H-h)/2,{R.GRADE}")
    cmd = ["ffmpeg", "-v", "error", "-stream_loop", "-1", "-ss", f"{max(0.0, start):.3f}", "-i", path,
           "-frames:v", str(n), "-filter_complex", vf, "-an", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"]
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, bufsize=W * H * 3)
    last, got = None, 0
    while got < n:
        buf = p.stdout.read(W * H * 3)
        if len(buf) < W * H * 3:
            break
        last = Image.frombuffer("RGB", (W, H), buf, "raw", "RGB", 0, 1)
        got += 1
        yield last
    p.stdout.close()
    p.wait()
    while got < n and last is not None:
        got += 1
        yield last


# ------------------------------------------------------------------ plan / render
def load_plan(path):
    plan = json.load(open(path))
    root = os.path.dirname(os.path.abspath(path))
    for s in plan["scenes"]:
        for k in ("path", "bg_path"):
            if s.get(k) and not os.path.isabs(s[k]):
                s[k] = os.path.join(root, s[k])
    plan["root"] = root
    return plan


def make_scene(s, plan):
    t = s["type"]
    if t in ("photo", "video"):
        return Media(s)
    if t == "map":
        return MapScene(s, os.path.join(plan["root"], "geo"))
    return Card(s)


def scene_frames(s, obj, plan, captions, f_from=None, f_to=None):
    """Yield (global_frame, RGB frame) for scene s."""
    f0, f1 = int(round(s["start"] * FPS)), int(round(s["end"] * FPS))
    a, b = max(f0, f_from if f_from is not None else f0), min(f1, f_to if f_to is not None else f1)
    n = f1 - f0
    dur = s["end"] - s["start"]
    gen = obj.frames(n) if isinstance(obj, Media) else None
    for j in range(n):
        base = next(gen) if gen is not None else None
        gf = f0 + j
        if gf < a:
            continue
        if gf >= b:
            break
        t = gf / FPS
        lt = t - s["start"]
        if isinstance(obj, Media):
            c = obj.draw_frame(base, t, lt, dur)
        elif isinstance(obj, MapScene):
            c = Image.new("RGBA", (W, H))
            obj.draw(c, t, lt, dur)
            blit(c, R.BOTTOM_SCRIM, 0, H - R.BOTTOM_SCRIM.height, 0.8)
        else:
            c = obj.background(t, lt, dur)
            obj.draw(c, lt, dur)
        credit_draw(c, s.get("credit"), lt, dur)
        captions.draw(c, t)
        yield gf, c.convert("RGB")


def build_captions(plan):
    hide = [(s["start"], s["end"]) for s in plan["scenes"] if s["type"] not in CAPTION_TYPES]
    return Captions(plan["tokens"], hide)


def encoder(out, n_frames):
    return subprocess.Popen(
        ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
         "-i", "-", "-vf", "scale=out_color_matrix=bt709:out_range=tv,format=yuv420p",
         "-c:v", "libx264", "-preset", "faster", "-crf", "19", "-profile:v", "high", "-level", "4.2",
         "-g", "60", "-keyint_min", "60", "-sc_threshold", "0", "-bf", "2",
         "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709",
         "-frames:v", str(n_frames), "-an", out], stdin=subprocess.PIPE)


def render_slice(plan, k, out):
    f_from, f_to = plan["slices"][k]
    captions = build_captions(plan)
    enc = encoder(out, f_to - f_from)
    written = 0
    last = None
    for s in plan["scenes"]:
        f0, f1 = int(round(s["start"] * FPS)), int(round(s["end"] * FPS))
        if f1 <= f_from or f0 >= f_to:
            continue
        obj = make_scene(s, plan)
        for gf, fr in scene_frames(s, obj, plan, captions, f_from, f_to):
            enc.stdin.write(fr.tobytes())
            written += 1
            last = fr
            if written % 300 == 0:
                print(f"  slice {k}: {written}/{f_to - f_from} frames", flush=True)
    while written < f_to - f_from and last is not None:
        enc.stdin.write(last.tobytes())
        written += 1
    enc.stdin.close()
    if enc.wait() != 0:
        sys.exit("encoder failed")
    print(f"slice {k}: wrote {out} ({written} frames)")


def stills(plan, times, outdir):
    os.makedirs(outdir, exist_ok=True)
    captions = build_captions(plan)
    for t in times:
        s = next(x for x in plan["scenes"] if x["start"] <= t < x["end"])
        obj = make_scene(s, plan)
        gf = int(round(t * FPS))
        for g, fr in scene_frames(s, obj, plan, captions, gf, gf + 1):
            fr.save(os.path.join(outdir, f"still_{t:07.2f}.png"))


def thumbnail(plan, out):
    th = plan.get("thumbnail", {})
    c = studio(3.0).convert("RGBA")
    if th.get("bg_path") and th.get("sharp"):
        return thumbnail_photo(plan, th, c, out)
    if th.get("bg_path"):
        c = BlurBG(os.path.join(plan["root"], th["bg_path"])).frame(0, 1)
    d = ImageDraw.Draw(c)
    big = th.get("big", "$7")
    f = font(BLACK, R.fit_size(BLACK, big, 900, 620, 200))
    cap = R.cap_height(f)
    spr = shadowed((int(f.getlength(big)) + 120, cap + 160), [(60, 60 + cap, big, f, ACCENT, 0)],
                   ((0, 14, 34, 0.6), (0, 4, 6, 0.35)))
    blit(c, spr, W - M - spr.width + 60, H / 2 - cap / 2 - 60 - 20)
    top = int(H * 0.30)
    k = Kicker(th.get("kicker", "The full story"), 46)
    blit(c, k.img, M - k.pad, top - k.pad)
    top += k.cap + 50
    tb = TextBlock(th.get("text", "The *Rock*"), BLACK, 190, 900, max_lines=2, leading=0.98)
    tb.draw(c, M, top, 5.0)
    sub = th.get("sub")
    if sub:
        sb = TextBlock(sub, BOLD, 72, 900, max_lines=2, color=WHITE)
        sb.draw(c, M, top + tb.height + 70, 5.0)
    d.rectangle((M, H - 120, M + 300, H - 108), fill=ACCENT + (255,))
    c.convert("RGB").resize((1280, 720), Image.LANCZOS).save(out, quality=92)
    print(f"thumbnail -> {out}")


def thumbnail_photo(plan, th, c, out):
    """Sharp photo filling the right side (fading into the dark studio), big title on the left."""
    img = Image.open(os.path.join(plan["root"], th["bg_path"])).convert("RGB")
    x0 = int(W * 0.36)
    rw, rh = W - x0, H
    sc = max(rw / img.width, rh / img.height)
    img = img.resize((int(img.width * sc) + 1, int(img.height * sc) + 1), Image.LANCZOS)
    fx, fy = th.get("focus", (0.5, 0.25))
    cx, cy = int((img.width - rw) * fx), int((img.height - rh) * fy)
    ph = img.crop((cx, cy, cx + rw, cy + rh)).convert("RGBA")
    ramp = np.clip(np.linspace(0, 1, rw) / 0.42, 0, 1) ** 1.6
    a = np.tile((ramp * 255).astype(np.uint8), (rh, 1))
    ph.putalpha(Image.fromarray(a, "L"))
    c.alpha_composite(ph, (x0, 0))
    blit(c, R.vgrad(360, 0.0, 0.55, power=1.4), 0, H - 360)
    top = int(H * 0.25)
    k = Kicker(th.get("kicker", "The full story"), 46)
    blit(c, k.img, M - k.pad, top - k.pad)
    top += k.cap + 50
    tb = TextBlock(th.get("text", "The *Rock*"), BLACK, th.get("size", 200), 980, max_lines=2, leading=0.98)
    tb.draw(c, M, top, 5.0)
    if th.get("sub"):
        sb = TextBlock(th["sub"], BLACK, 96, 1000, max_lines=2, color=WHITE)
        sb.draw(c, M, top + tb.height + 64, 5.0)
    ImageDraw.Draw(c).rectangle((M, H - 120, M + 300, H - 108), fill=ACCENT + (255,))
    c.convert("RGB").resize((1280, 720), Image.LANCZOS).save(out, quality=92)
    print(f"thumbnail -> {out}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("plan")
    ap.add_argument("out")
    ap.add_argument("--slice", type=int)
    ap.add_argument("--stills")
    ap.add_argument("--thumb", action="store_true")
    a = ap.parse_args()
    plan = load_plan(a.plan)
    if a.thumb:
        thumbnail(plan, a.out)
    elif a.stills:
        stills(plan, [float(x) for x in a.stills.split(",")], a.out)
    else:
        render_slice(plan, a.slice, a.out)
