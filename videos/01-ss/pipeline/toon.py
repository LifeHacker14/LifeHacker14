"""Cartoon drawing kit: our own mascot, generic people, props, scenes. Drawn with PIL at 1920x1080."""
import math
from PIL import Image, ImageDraw, ImageFont, ImageFilter

S = "/tmp/claude-0/-home-user-LifeHacker14/90ebba43-d755-5558-a675-5caff7c9482b/scratchpad/sample"
HAND = f"{S}/data/gf/ofl/patrickhand/PatrickHand-Regular.ttf"
HANDSC = f"{S}/data/gf/ofl/patrickhandsc/PatrickHandSC-Regular.ttf"
W, H = 1920, 1080
INK = (52, 44, 40); SKIN = (247, 214, 184); CREAM = (250, 246, 238); RED = (200, 40, 40)
GREYBG = (204, 204, 202)
_F = {}


def F(s, sc=False):
    s = max(2, int(s))
    k = (s, sc)
    if k not in _F: _F[k] = ImageFont.truetype(HANDSC if sc else HAND, s)
    return _F[k]


def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def ease(x): x = clamp(x); return 1 - (1 - x) ** 3
def back(x):  # overshoot pop
    x = clamp(x); c = 1.7; return 1 + (c + 1) * (x - 1) ** 3 + c * (x - 1) ** 2
def lerp(a, b, t): return a + (b - a) * t


# ---------------- backgrounds ----------------
def grey_bg():
    return Image.new("RGB", (W, H), GREYBG)


def sky_bg(ground=(122, 186, 90), horizon=760, sky_top=(120, 180, 230), sky_bot=(196, 226, 246), hills=True, t=0):
    img = Image.new("RGB", (W, H)); d = ImageDraw.Draw(img)
    for y in range(horizon):
        k = y / horizon; d.line([0, y, W, y], fill=tuple(int(lerp(a, b, k)) for a, b in zip(sky_top, sky_bot)))
    if hills:
        d.ellipse([-300, horizon - 160, 900, horizon + 260], fill=(148, 200, 110))
        d.ellipse([700, horizon - 120, 2300, horizon + 300], fill=(136, 192, 100))
    d.rectangle([0, horizon, W, H], fill=ground)
    for cx, cy, s in [(300, 150, 1), (1500, 110, .8), (1100, 230, .6)]:
        cloud(d, cx + 12 * t, cy, s)
    return img


def dusk_bg(horizon=820):
    return sky_bg(ground=(40, 34, 44), horizon=horizon, sky_top=(46, 40, 78), sky_bot=(236, 140, 84), hills=False)


def cloud(d, x, y, s=1.0):
    for dx, dy, r in [(-60, 10, 46), (0, -14, 60), (64, 6, 48), (20, 22, 44)]:
        d.ellipse([x + (dx - r) * s, y + (dy - r) * s, x + (dx + r) * s, y + (dy + r) * s], fill=(255, 255, 255))


def room_bg(wall=(232, 220, 196), floor=(150, 104, 66)):
    img = Image.new("RGB", (W, H), wall); d = ImageDraw.Draw(img)
    d.polygon([(0, 760), (W, 760), (W, H), (0, H)], fill=floor)
    d.line([0, 760, W, 760], fill=INK, width=6)
    d.rectangle([0, 0, W, 40], fill=(120, 84, 52)); d.rectangle([0, 0, 40, 760], fill=(120, 84, 52)); d.rectangle([W - 40, 0, W, 760], fill=(120, 84, 52))
    return img


# ---------------- text ----------------
def hand_text(img, xy, s, size, t=1.0, fill=INK, anchor="mm", sc=False, cps=26):
    """handwritten text that writes itself on"""
    if t <= 0: return
    n = int(len(s) * clamp(t * cps / max(1, len(s))))
    d = ImageDraw.Draw(img); f = F(size, sc)
    full = d.textbbox((0, 0), s, font=f, anchor="lt")
    x, y = xy
    if anchor == "mm": x -= (full[2] - full[0]) / 2; y -= (full[3] - full[1]) / 2
    d.text((x, y), s[:n], font=f, fill=fill, anchor="lt")


def badge(img, s, t=1.0):
    if t <= 0: return
    d = ImageDraw.Draw(img, "RGBA"); f = F(40); w = d.textlength(s, font=f)
    a = int(220 * ease(t * 3))
    d.rounded_rectangle([40, 36, 40 + w + 36, 96], 8, fill=(70, 70, 74, a))
    d.text((58, 66), s, font=f, fill=(245, 245, 245, a), anchor="lm")


def bubble(img, xy, s, t=1.0, size=44):
    if t <= 0: return
    d = ImageDraw.Draw(img); f = F(size); a = back(t * 3)
    lines = s.split("\n"); w = max(d.textlength(l, font=f) for l in lines) + 50; h = len(lines) * size * 1.05 + 34
    x, y = xy; w *= a; h *= a
    d.rounded_rectangle([x - w / 2, y - h, x + w / 2, y], 22, fill=(255, 255, 255), outline=INK, width=4)
    d.polygon([(x - 14, y - 2), (x + 14, y - 2), (x - 6, y + 26)], fill=(255, 255, 255), outline=INK)
    d.line([x - 13, y - 3, x + 13, y - 3], fill=(255, 255, 255), width=5)
    if a > .9:
        for i, l in enumerate(lines): d.text((x, y - h + 17 + i * size * 1.05), l, font=f, fill=INK, anchor="mt")


def tag(img, xy, s, t=1.0, size=34):
    if t <= 0: return
    d = ImageDraw.Draw(img, "RGBA"); f = F(size); w = d.textlength(s, font=f); a = int(255 * ease(t * 3))
    d.rounded_rectangle([xy[0] - w / 2 - 16, xy[1] - 24, xy[0] + w / 2 + 16, xy[1] + 24], 12, fill=(70, 70, 74, int(a * .85)))
    d.text(xy, s, font=f, fill=(250, 250, 250, a), anchor="mm")


# ---------------- people ----------------
def person(img, x, y, s=1.0, coat=(70, 90, 140), trousers=(60, 60, 70), hat=None, hair=(90, 60, 40), mustache=False,
           mouth=0.0, arm=0.0, face=0, blink=False, skin=SKIN, alpha=1.0):
    """generic cartoon person standing with feet at (x, y). arm: 0 down, 1 pointing outward. face: -1 left, 0 front, 1 right"""
    if alpha <= 0: return
    layer = Image.new("RGBA", (int(340 * s), int(560 * s)), (0, 0, 0, 0)); d = ImageDraw.Draw(layer)
    cx = layer.width / 2; by = layer.height - 10 * s
    lw = max(2, int(5 * s))
    # legs
    for dx in (-22, 22):
        d.line([cx + dx * s, by - 150 * s, cx + dx * s, by - 12 * s], fill=INK, width=lw)
        d.ellipse([cx + (dx - 18) * s, by - 22 * s, cx + (dx + 18) * s, by], fill=INK)
    # body (coat)
    top, bot = by - 330 * s, by - 140 * s
    d.rounded_rectangle([cx - 58 * s, top, cx + 58 * s, bot], int(26 * s), fill=coat, outline=INK, width=lw)
    d.rectangle([cx - 56 * s, bot - 34 * s, cx + 56 * s, bot - 2 * s], fill=trousers)
    d.line([cx - 56 * s, bot - 34 * s, cx + 56 * s, bot - 34 * s], fill=INK, width=lw)
    d.line([cx, top + 20 * s, cx, bot - 36 * s], fill=INK, width=max(1, lw // 2))
    # arms
    sx = cx + 58 * s * (1 if face >= 0 else -1)
    ang = math.radians(lerp(80, 10, arm))
    ex = sx + math.cos(ang) * 150 * s * (1 if face >= 0 else -1); ey = top + 30 * s + math.sin(ang) * 150 * s
    d.line([sx, top + 30 * s, ex, ey], fill=coat, width=int(26 * s)); d.ellipse([ex - 14 * s, ey - 14 * s, ex + 14 * s, ey + 14 * s], fill=skin, outline=INK, width=max(1, lw // 2))
    ox = cx - 58 * s * (1 if face >= 0 else -1)
    d.line([ox, top + 30 * s, ox - 18 * s * (1 if face >= 0 else -1), top + 160 * s], fill=coat, width=int(26 * s))
    d.ellipse([ox - 18 * s * (1 if face >= 0 else -1) - 14 * s, top + 146 * s, ox - 18 * s * (1 if face >= 0 else -1) + 14 * s, top + 174 * s], fill=skin, outline=INK, width=max(1, lw // 2))
    # head
    hr = 64 * s; hy = top - hr + 10 * s
    d.ellipse([cx - hr, hy - hr, cx + hr, hy + hr], fill=skin, outline=INK, width=lw)
    if hair: d.chord([cx - hr, hy - hr, cx + hr, hy + hr], 190, 350, fill=hair, outline=INK, width=lw)
    fx = cx + face * 14 * s
    if blink:
        for ex2 in (-22, 22): d.line([fx + (ex2 - 8) * s, hy, fx + (ex2 + 8) * s, hy], fill=INK, width=lw)
    else:
        for ex2 in (-22, 22): d.ellipse([fx + (ex2 - 7) * s, hy - 9 * s, fx + (ex2 + 7) * s, hy + 9 * s], fill=INK)
    if mustache: d.rectangle([fx - 12 * s, hy + 22 * s, fx + 12 * s, hy + 32 * s], fill=INK)
    mo = clamp(mouth)
    if mo > .15: d.ellipse([fx - 14 * s, hy + 34 * s, fx + 14 * s, hy + (40 + 26 * mo) * s], fill=(120, 30, 30), outline=INK, width=max(1, lw // 2))
    else: d.arc([fx - 18 * s, hy + 20 * s, fx + 18 * s, hy + 44 * s], 20, 160, fill=INK, width=lw)
    # hats
    if hat == "cap":  # dark peaked cap, no insignia
        d.chord([cx - hr * 1.02, hy - hr * 1.1, cx + hr * 1.02, hy + hr * .5], 180, 360, fill=(36, 36, 40), outline=INK, width=lw)
        d.rectangle([cx - hr * 1.05, hy - hr * .32, cx + hr * 1.05, hy - hr * .18], fill=(36, 36, 40))
        d.polygon([(cx - hr * .2, hy - hr * .2), (cx + hr * 1.25 * (1 if face >= 0 else -1), hy - hr * .1), (cx + hr * .4, hy - hr * .05)], fill=INK)
    elif hat == "flat":  # worker's flat cap
        d.chord([cx - hr * 1.05, hy - hr * 1.05, cx + hr * 1.05, hy + hr * .4], 180, 360, fill=(110, 90, 70), outline=INK, width=lw)
        d.ellipse([cx, hy - hr * .35, cx + hr * 1.3, hy - hr * .05], fill=(110, 90, 70), outline=INK, width=max(1, lw // 2))
    elif hat == "helmet":
        d.chord([cx - hr * 1.15, hy - hr * 1.15, cx + hr * 1.15, hy + hr * .6], 180, 360, fill=(90, 100, 80), outline=INK, width=lw)
    elif hat == "police":
        d.rectangle([cx - hr * .8, hy - hr * 1.5, cx + hr * .8, hy - hr * .55], fill=(30, 50, 90), outline=INK, width=lw)
        d.rectangle([cx - hr, hy - hr * .65, cx + hr, hy - hr * .45], fill=INK)
    a = Image.new("L", layer.size, 0); a.paste(layer.getchannel("A").point(lambda v: int(v * alpha)))
    layer.putalpha(a)
    img.paste(layer, (int(x - layer.width / 2), int(y - layer.height + 10 * s)), layer)


def mascot(img, x, y, s=1.0, mouth=0.0, point=0.0, blink=False, look=1):
    """OUR mascot: 'the Archivist' - round glasses, green scarf, brown cardigan, holding a rolled scroll."""
    layer = Image.new("RGBA", (int(420 * s), int(620 * s)), (0, 0, 0, 0)); d = ImageDraw.Draw(layer)
    cx = layer.width / 2; by = layer.height - 10 * s; lw = max(2, int(5 * s))
    for dx in (-24, 24):
        d.line([cx + dx * s, by - 160 * s, cx + dx * s, by - 14 * s], fill=INK, width=lw + 2)
        d.ellipse([cx + (dx - 22) * s, by - 24 * s, cx + (dx + 22) * s, by], fill=(90, 60, 40), outline=INK, width=2)
    top, bot = by - 350 * s, by - 150 * s
    d.rounded_rectangle([cx - 66 * s, top, cx + 66 * s, bot], int(34 * s), fill=(150, 104, 62), outline=INK, width=lw)
    d.rectangle([cx - 64 * s, bot - 30 * s, cx + 64 * s, bot - 2 * s], fill=(70, 70, 80))
    for k in range(4): d.ellipse([cx - 6 * s, top + (50 + k * 30) * s, cx + 6 * s, top + (62 + k * 30) * s], fill=(240, 220, 160))
    # scarf
    d.rounded_rectangle([cx - 60 * s, top - 6 * s, cx + 60 * s, top + 26 * s], int(12 * s), fill=(40, 130, 90), outline=INK, width=lw)
    d.polygon([(cx + 20 * s, top + 20 * s), (cx + 48 * s, top + 20 * s), (cx + 56 * s, top + 120 * s), (cx + 30 * s, top + 116 * s)], fill=(40, 130, 90), outline=INK)
    # arms: right arm points with scroll
    sx = cx + 66 * s; ang = math.radians(lerp(78, -20, point))
    ex = sx + math.cos(ang) * 160 * s; ey = top + 36 * s + math.sin(ang) * 160 * s
    d.line([sx, top + 36 * s, ex, ey], fill=(150, 104, 62), width=int(30 * s))
    d.line([ex, ey, ex + 70 * s * math.cos(ang - .3), ey + 70 * s * math.sin(ang - .3)], fill=(236, 222, 190), width=int(18 * s))
    d.ellipse([ex - 16 * s, ey - 16 * s, ex + 16 * s, ey + 16 * s], fill=SKIN, outline=INK, width=2)
    ox = cx - 66 * s
    d.line([ox, top + 36 * s, ox - 22 * s, top + 170 * s], fill=(150, 104, 62), width=int(30 * s))
    d.ellipse([ox - 38 * s, top + 154 * s, ox - 6 * s, top + 186 * s], fill=SKIN, outline=INK, width=2)
    # head (bigger, rounder)
    hr = 82 * s; hy = top - hr + 14 * s
    d.ellipse([cx - hr, hy - hr, cx + hr, hy + hr], fill=SKIN, outline=INK, width=lw)
    for k in (-1, 1):  # grey side hair tufts
        d.ellipse([cx + k * hr * .78 - 26 * s, hy - 40 * s, cx + k * hr * .78 + 26 * s, hy + 16 * s], fill=(200, 200, 205), outline=INK, width=2)
    d.arc([cx - 30 * s, hy - hr - 18 * s, cx + 30 * s, hy - hr + 30 * s], 200, 340, fill=INK, width=lw)
    fx = cx + look * 10 * s
    for ex2 in (-30, 30):  # round glasses
        d.ellipse([fx + (ex2 - 24) * s, hy - 24 * s, fx + (ex2 + 24) * s, hy + 24 * s], fill=(236, 244, 250), outline=INK, width=lw)
        if blink: d.line([fx + (ex2 - 9) * s, hy, fx + (ex2 + 9) * s, hy], fill=INK, width=lw)
        else: d.ellipse([fx + (ex2 - 8 + look * 4) * s, hy - 9 * s, fx + (ex2 + 8 + look * 4) * s, hy + 9 * s], fill=INK)
    d.line([fx - 6 * s, hy, fx + 6 * s, hy], fill=INK, width=lw)
    for ex2 in (-30, 30): d.line([fx + (ex2 - 18) * s, hy - 36 * s, fx + (ex2 + 14) * s, hy - 40 * s], fill=INK, width=lw)
    mo = clamp(mouth)
    if mo > .12: d.ellipse([fx - 18 * s, hy + 38 * s, fx + 18 * s, hy + (44 + 34 * mo) * s], fill=(130, 36, 36), outline=INK, width=lw)
    else: d.arc([fx - 22 * s, hy + 28 * s, fx + 22 * s, hy + 54 * s], 20, 160, fill=INK, width=lw)
    img.paste(layer, (int(x - layer.width / 2), int(y - layer.height + 10 * s)), layer)


# ---------------- props / icons ----------------
def framed(img, photo, box, t=1.0, caption=None):
    if t <= 0: return
    x0, y0, x1, y1 = box; a = back(t * 3)
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2; w, h = (x1 - x0) * a, (y1 - y0) * a
    if w < 4: return
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([cx - w / 2 - 12, cy - h / 2 - 12, cx + w / 2 + 12, cy + h / 2 + 12], 14, fill=(60, 60, 64))
    from PIL import ImageOps
    img.paste(ImageOps.fit(photo, (int(w), int(h))), (int(cx - w / 2), int(cy - h / 2)))
    if caption and t > .3: d.text((cx, cy + h / 2 + 44), caption, font=F(44), fill=INK, anchor="mm")


def icon(img, kind, x, y, s=1.0, t=1.0, label=None):
    if t <= 0: return
    s *= back(t * 3); d = ImageDraw.Draw(img); lw = max(2, int(5 * s))
    if kind == "police":
        d.rounded_rectangle([x - 70 * s, y - 40 * s, x + 70 * s, y + 30 * s], int(14 * s), fill=(30, 50, 90), outline=INK, width=lw)
        d.rectangle([x - 90 * s, y + 20 * s, x + 90 * s, y + 46 * s], fill=INK)
        d.polygon([(x, y - 26 * s), (x + 16 * s, y - 4 * s), (x, y + 14 * s), (x - 16 * s, y - 4 * s)], fill=(230, 200, 90))
    elif kind == "camp":
        for k in range(-3, 4): d.line([x + k * 30 * s, y - 50 * s, x + k * 30 * s, y + 50 * s], fill=INK, width=lw)
        for yy in (-30, 0, 30): d.line([x - 100 * s, y + yy * s, x + 100 * s, y + yy * s], fill=(120, 120, 120), width=max(1, lw - 2))
        d.rectangle([x + 60 * s, y - 140 * s, x + 110 * s, y - 80 * s], fill=(110, 90, 70), outline=INK, width=lw)
        d.line([x + 70 * s, y - 80 * s, x + 66 * s, y + 50 * s], fill=INK, width=lw); d.line([x + 100 * s, y - 80 * s, x + 104 * s, y + 50 * s], fill=INK, width=lw)
    elif kind == "factory":
        d.rectangle([x - 100 * s, y - 30 * s, x + 100 * s, y + 50 * s], fill=(170, 90, 70), outline=INK, width=lw)
        d.polygon([(x - 100 * s, y - 30 * s), (x - 60 * s, y - 70 * s), (x - 60 * s, y - 30 * s), (x - 20 * s, y - 70 * s), (x - 20 * s, y - 30 * s), (x + 20 * s, y - 70 * s), (x + 20 * s, y - 30 * s)], fill=(170, 90, 70), outline=INK)
        d.rectangle([x + 50 * s, y - 130 * s, x + 80 * s, y - 30 * s], fill=(130, 70, 56), outline=INK, width=lw)
        for k in range(3): d.ellipse([x + (50 + k * 18) * s, y - (170 + k * 30) * s, x + (90 + k * 22) * s, y - (136 + k * 30) * s], fill=(160, 160, 160))
    elif kind == "army":
        d.chord([x - 90 * s, y - 80 * s, x + 90 * s, y + 70 * s], 180, 360, fill=(90, 100, 80), outline=INK, width=lw)
        d.line([x - 110 * s, y - 2 * s, x + 110 * s, y - 2 * s], fill=INK, width=lw + 2)
    elif kind == "money":
        d.ellipse([x - 70 * s, y - 50 * s, x + 70 * s, y + 70 * s], fill=(200, 170, 100), outline=INK, width=lw)
        d.polygon([(x - 30 * s, y - 50 * s), (x + 30 * s, y - 50 * s), (x + 14 * s, y - 80 * s), (x - 14 * s, y - 80 * s)], fill=(200, 170, 100), outline=INK)
        d.text((x, y + 14 * s), "M", font=F(int(70 * s)), fill=INK, anchor="mm")
    elif kind == "bread":
        d.rounded_rectangle([x - 80 * s, y - 40 * s, x + 80 * s, y + 40 * s], int(36 * s), fill=(214, 160, 90), outline=INK, width=lw)
        for k in (-40, 0, 40): d.line([x + (k - 14) * s, y - 24 * s, x + (k + 14) * s, y + 10 * s], fill=INK, width=max(1, lw - 2))
    if label: d.text((x, y + 110 * s / max(.01, back(t * 3))), label, font=F(48), fill=INK, anchor="mm")
