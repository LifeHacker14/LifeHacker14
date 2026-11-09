"""Scene templates for the full SS video. Every template: fn(img, sh) where sh = Shot (see full.py)."""
import math, json, os, sys
from PIL import Image, ImageDraw, ImageOps, ImageEnhance, ImageFilter
SAMPLE = "/tmp/claude-0/-home-user-LifeHacker14/90ebba43-d755-5558-a675-5caff7c9482b/scratchpad/sample"
sys.path.insert(0, SAMPLE)
from toon import *

VID = "/tmp/claude-0/-home-user-LifeHacker14/90ebba43-d755-5558-a675-5caff7c9482b/scratchpad/video"
WHITE = (255, 255, 255)

# ---------------- characters ----------------
SSMAN = dict(coat=(38, 38, 42), trousers=(28, 28, 32), hat="cap", collar=(60, 60, 64))
SA = dict(coat=(150, 110, 60), trousers=(100, 80, 50), hat="flat", collar=(150, 110, 60))
HITLER = dict(coat=(150, 118, 76), trousers=(80, 66, 50), hair=(50, 34, 24), mustache=True)
HIMMLER = dict(coat=(38, 38, 42), trousers=(28, 28, 32), hat="cap", collar=(60, 60, 64), glasses=True, mustache=True)
HEYDRICH = dict(coat=(38, 38, 42), trousers=(28, 28, 32), hat="cap", collar=(60, 60, 64), hair=(220, 200, 140))
ROHM = dict(coat=(150, 110, 60), trousers=(100, 80, 50), hair=(60, 40, 30), collar=(150, 110, 60))
OFFICIAL = dict(coat=(90, 90, 98), trousers=(70, 70, 76), hair=(80, 70, 60))
SOLDIER = dict(coat=(110, 116, 96), trousers=(80, 84, 70), hat="helmet", collar=(110, 116, 96))
POLICE = dict(coat=(40, 70, 60), trousers=(40, 50, 46), hat="police", collar=(40, 70, 60))
WORKER = dict(coat=(90, 100, 130), trousers=(60, 60, 70), hat="flat")
BRIT = dict(coat=(120, 110, 70), trousers=(90, 84, 56), hat="helmet", collar=(120, 110, 70))
JUDGE = dict(coat=(30, 30, 34), trousers=(30, 30, 34), hair=(220, 220, 220), collar=(250, 250, 250))
CHARS = dict(ss=SSMAN, sa=SA, hitler=HITLER, himmler=HIMMLER, heydrich=HEYDRICH, rohm=ROHM, official=OFFICIAL, soldier=SOLDIER,
             police=POLICE, worker=WORKER, brit=BRIT, judge=JUDGE, eicke=SSMAN, goring=dict(coat=(120, 130, 150), trousers=(90, 96, 110), hair=(90, 70, 50)),
             bernadotte=dict(coat=(70, 80, 100), trousers=(60, 64, 80), hair=(150, 130, 100)), eichmann=dict(coat=(90, 90, 98), trousers=(70, 70, 76), hair=(60, 50, 40), glasses=True))

# ---------------- maps ----------------
LAT0 = math.cos(math.radians(50))
def load_sat(path, lon0, lon1, lat0, lat1, squeeze):
    im = Image.open(path).convert("RGB"); im = im.resize((int(im.width * squeeze), im.height), Image.LANCZOS)
    return ImageEnhance.Color(im).enhance(1.15), (lon0, lon1, lat0, lat1)
EU, EUB = load_sat(f"{SAMPLE}/sat/eu.jpg", -12, 42, 34, 63, LAT0)
WORLD, WB = load_sat(f"{SAMPLE}/sat/world.jpg", -100, 60, -60, 70, 1.0)
GEO = {y: json.load(open(f"{SAMPLE}/data/hb/geojson/world_{y}.geojson"))["features"] for y in (1914, 1920, 1938)}

def proj(base, b, lo, la): return ((lo - b[0]) / (b[1] - b[0]) * base.width, (b[3] - la) / (b[3] - b[2]) * base.height)

_MAPCACHE = {}
def map_img(key, fills, year=1938, base="eu", dark=0.0):
    if key in _MAPCACHE: return _MAPCACHE[key]
    im, b = (EU, EUB) if base == "eu" else (WORLD, WB)
    out = im.copy().convert("RGBA"); ov = Image.new("RGBA", out.size, (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
    def polys(yr, name):
        for f in GEO[yr]:
            if f["properties"].get("NAME") == name:
                g = f["geometry"]; cs = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
                for poly in cs: yield [proj(im, b, *pt[:2]) for pt in poly[0]]
    if year:
        for f in GEO[year]:
            g = f["geometry"]; cs = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
            for poly in cs:
                pts = [proj(im, b, *pt[:2]) for pt in poly[0]]
                if len(pts) > 2: d.line(pts + [pts[0]], fill=(255, 255, 255, 70), width=2)
    for yr, name, col in fills:
        for pts in polys(yr, name):
            if len(pts) > 2: d.polygon(pts, fill=col); d.line(pts + [pts[0]], fill=(255, 255, 255, 210), width=3)
    out = Image.alpha_composite(out, ov).convert("RGB")
    if dark: out = ImageEnhance.Brightness(ImageEnhance.Color(out).enhance(.3)).enhance(1 - dark)
    _MAPCACHE[key] = (out, b); return out, b

def cam(img, cx, cy, vw):
    vw = min(vw, img.width, img.height * W / H); vh = vw * H / W
    cx = clamp(cx, vw / 2, img.width - vw / 2); cy = clamp(cy, vh / 2, img.height - vh / 2)
    box = (cx - vw / 2, cy - vh / 2, cx + vw / 2, cy + vh / 2)
    return img.resize((W, H), Image.BICUBIC, box=box), box

def to_screen(box, x, y): sc = W / (box[2] - box[0]); return (x - box[0]) * sc, (y - box[1]) * sc

def pin(img, x, y, t, col=(240, 196, 40)):
    if t <= 0: return
    d = ImageDraw.Draw(img); a = back(t * 3); yy = y - (1 - ease(t * 3)) * 90; r = 22 * a
    d.ellipse([x - r, yy - 64 * a, x + r, yy - 20 * a], fill=col, outline=INK, width=3)
    d.polygon([(x - r * .8, yy - 34 * a), (x + r * .8, yy - 34 * a), (x, yy)], fill=col, outline=INK)
    d.ellipse([x - 7 * a, yy - 49 * a, x + 7 * a, yy - 35 * a], fill=INK)

# ---------------- photos ----------------
def photo(p): return ImageEnhance.Contrast(ImageOps.grayscale(Image.open(p)).convert("RGB")).enhance(1.15)
PHOTOS = {"himmler": photo(f"{VID}/img/10.jpg"), "beer": photo(f"{VID}/img/01.jpg")}

# ---------------- drawing helpers ----------------
def buildings(img, horizon=760, dark=False, broken=False, seed=0):
    d = ImageDraw.Draw(img)
    cols = [(196, 120, 90), (210, 180, 130), (170, 140, 120), (200, 150, 100), (150, 120, 110)]
    if dark: cols = [(70, 60, 70), (80, 72, 76), (64, 58, 66), (76, 66, 70), (58, 52, 60)]
    x = -40
    for i in range(9):
        w = 230 + ((i + seed) * 37) % 80; h = 330 + ((i + seed) * 53) % 160
        d.rectangle([x, horizon - h, x + w, horizon], fill=cols[i % 5], outline=INK, width=4)
        for r in range(3):
            for c in range(3):
                wx = x + 30 + c * (w - 60) / 3; wy = horizon - h + 40 + r * 90
                if wy < horizon - 70:
                    glass = (40, 40, 50) if broken and (r + c + i) % 2 else ((70, 110, 160) if not dark else (230, 200, 120) if (r * c + i) % 3 == 0 else (40, 40, 50))
                    d.rectangle([wx, wy, wx + 40, wy + 56], fill=glass, outline=INK, width=3)
                    if broken and (r + c + i) % 2: d.line([wx + 6, wy + 6, wx + 34, wy + 48], fill=(200, 200, 210), width=2); d.line([wx + 34, wy + 10, wx + 10, wy + 40], fill=(200, 200, 210), width=2)
        x += w - 4
    d.rectangle([0, horizon, W, H], fill=(150, 150, 150) if not dark else (60, 60, 64)); d.line([0, horizon, W, horizon], fill=INK, width=5)

def ruins(img, horizon=800):
    d = ImageDraw.Draw(img)
    for i in range(12):
        x = i * 170 - 40; h = 120 + (i * 97) % 260
        pts = [(x, horizon), (x, horizon - h), (x + 40, horizon - h + 30), (x + 70, horizon - h - 20), (x + 110, horizon - h + 50), (x + 150, horizon - h + 10), (x + 150, horizon)]
        d.polygon(pts, fill=(84, 78, 76), outline=INK)
        for k in range(2): d.rectangle([x + 30 + k * 60, horizon - h + 80, x + 60 + k * 60, horizon - h + 130], fill=(30, 28, 30))
    d.rectangle([0, horizon, W, H], fill=(110, 104, 98));
    for k in range(18): d.ellipse([k * 110, horizon + 20 + (k % 3) * 30, k * 110 + 90, horizon + 60 + (k % 3) * 30], fill=(130, 122, 116), outline=INK)

def podium(img, x, y):
    d = ImageDraw.Draw(img)
    d.polygon([(x - 120, y - 260), (x + 120, y - 260), (x + 90, y), (x - 90, y)], fill=(120, 80, 50), outline=INK, width=5)
    d.rectangle([x - 140, y - 290, x + 140, y - 256], fill=(140, 96, 60), outline=INK, width=5)

def crowd(img, n=14, y=1080, dark=False):
    d = ImageDraw.Draw(img)
    for i in range(n):
        x = i * 150 + (i % 2) * 40; r = 70 + (i * 13) % 20
        c = (60 + (i * 3) % 30, 52, 50) if not dark else (30, 28, 32)
        d.ellipse([x - r, y - 120 - (i % 3) * 14, x + r, y + 40], fill=c, outline=INK, width=4)

def table(img, x0, x1, y):
    d = ImageDraw.Draw(img)
    d.rectangle([x0, y, x1, y + 40], fill=(120, 80, 50), outline=INK, width=5)
    for x in (x0 + 30, x1 - 50): d.rectangle([x, y + 40, x + 20, y + 200], fill=(100, 66, 40), outline=INK, width=3)

def castle(img, cx=960, by=820):
    d = ImageDraw.Draw(img)
    d.polygon([(cx - 420, by), (cx - 420, by - 260), (cx + 420, by - 260), (cx + 420, by)], fill=(196, 186, 170), outline=INK)
    for x in (cx - 470, cx + 370):
        d.rectangle([x, by - 400, x + 100, by], fill=(186, 176, 160), outline=INK, width=5)
        d.polygon([(x - 10, by - 400), (x + 50, by - 500), (x + 110, by - 400)], fill=(90, 60, 50), outline=INK)
    d.ellipse([cx - 120, by - 470, cx + 120, by - 230], fill=(186, 176, 160), outline=INK, width=5)
    d.polygon([(cx - 130, by - 350), (cx, by - 560), (cx + 130, by - 350)], fill=(90, 60, 50), outline=INK)
    for k in range(-3, 4): d.rectangle([cx + k * 110 - 18, by - 200, cx + k * 110 + 18, by - 140], fill=(50, 50, 60), outline=INK, width=3)
    d.rectangle([cx - 50, by - 120, cx + 50, by], fill=(80, 56, 40), outline=INK, width=4)

def cabinet(img, x, y):
    d = ImageDraw.Draw(img)
    d.rectangle([x - 160, y - 520, x + 160, y], fill=(120, 120, 128), outline=INK, width=5)
    for k in range(4):
        d.rectangle([x - 140, y - 500 + k * 125, x + 140, y - 390 + k * 125], fill=(150, 150, 158), outline=INK, width=4)
        d.rectangle([x - 40, y - 455 + k * 125, x + 40, y - 440 + k * 125], fill=INK)

def card(img, cx, cy, label, t, rot=0):
    if t <= 0: return
    s = back(t * 3); L = Image.new("RGBA", (380, 230), (0, 0, 0, 0)); d = ImageDraw.Draw(L)
    d.rectangle([10, 10, 370, 220], fill=(252, 246, 224), outline=INK, width=5); d.line([30, 70, 350, 70], fill=(200, 80, 80), width=3)
    for k in range(3): d.line([30, 110 + k * 34, 350, 110 + k * 34], fill=(150, 180, 210), width=2)
    d.text((190, 40), label, font=F(44), fill=INK, anchor="mm")
    L = L.resize((max(1, int(380 * s)), max(1, int(230 * s)))).rotate(rot, expand=True, resample=Image.BICUBIC)
    img.paste(L, (int(cx - L.width / 2), int(cy - L.height / 2)), L)

def fire(img, x, y, now, s=1.0):
    d = ImageDraw.Draw(img)
    for k in range(5):
        h = (90 + 40 * math.sin(now * 9 + k)) * s; w = 40 * s
        xx = x + (k - 2) * 46 * s
        d.polygon([(xx - w, y), (xx, y - h), (xx + w, y)], fill=(240, 120 + k * 15, 40))
        d.polygon([(xx - w / 2, y), (xx, y - h * .55), (xx + w / 2, y)], fill=(255, 220, 90))

def bars(img, box):
    d = ImageDraw.Draw(img); x0, y0, x1, y1 = box
    d.rectangle(box, fill=(60, 60, 70), outline=INK, width=6)
    d.rectangle([x0 + 20, y0 + 20, x1 - 20, y1 - 20], fill=(150, 190, 230))
    for k in range(5): x = x0 + 20 + (k + 1) * (x1 - x0 - 40) / 6; d.line([x, y0 + 20, x, y1 - 20], fill=INK, width=10)

def chickens(img, now):
    d = ImageDraw.Draw(img)
    for i, x in enumerate((1250, 1420, 1580)):
        y = 900 + math.sin(now * 4 + i) * 6
        d.ellipse([x - 50, y - 60, x + 50, y + 10], fill=(250, 250, 245), outline=INK, width=4)
        d.ellipse([x + 20, y - 100, x + 70, y - 50], fill=(250, 250, 245), outline=INK, width=4)
        d.polygon([(x + 68, y - 80), (x + 92, y - 74), (x + 68, y - 68)], fill=(240, 170, 40))
        d.ellipse([x + 38, y - 112, x + 56, y - 96], fill=RED)
        d.line([x - 10, y + 10, x - 10, y + 40], fill=(240, 170, 40), width=5); d.line([x + 14, y + 10, x + 14, y + 40], fill=(240, 170, 40), width=5)

def barn(img, x, y):
    d = ImageDraw.Draw(img)
    d.rectangle([x - 180, y - 220, x + 180, y], fill=(176, 70, 56), outline=INK, width=5)
    d.polygon([(x - 210, y - 220), (x, y - 360), (x + 210, y - 220)], fill=(120, 50, 40), outline=INK)
    d.rectangle([x - 60, y - 140, x + 60, y], fill=(230, 220, 200), outline=INK, width=4)

def car(img, x, y, col=(50, 50, 56)):
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([x - 200, y - 110, x + 200, y - 30], 20, fill=col, outline=INK, width=5)
    d.rounded_rectangle([x - 110, y - 170, x + 110, y - 100], 20, fill=col, outline=INK, width=5)
    for wx in (x - 120, x + 120): d.ellipse([wx - 44, y - 74, wx + 44, y + 14], fill=(30, 30, 30), outline=INK, width=4)

def calendar(img, x, y, text, t):
    if t <= 0: return
    d = ImageDraw.Draw(img); s = back(t * 3)
    w, h = 420 * s, 360 * s
    d.rounded_rectangle([x - w / 2, y - h / 2, x + w / 2, y + h / 2], 24, fill=WHITE, outline=INK, width=6)
    d.rectangle([x - w / 2, y - h / 2, x + w / 2, y - h / 2 + 90 * s], fill=RED, outline=INK, width=6)
    if s > .8:
        lines = text.split("\n")
        for k, l in enumerate(lines): d.text((x, y + 30 + (k - (len(lines) - 1) / 2) * 90), l, font=F(100 if len(l) < 7 else 70), fill=INK, anchor="mm")
