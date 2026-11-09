"""Cartoon-explainer sample (79 s): our mascot, cartoon people, satellite maps, lip sync."""
import json, math, subprocess, sys, wave, os
import numpy as np
from PIL import Image, ImageDraw, ImageOps, ImageEnhance
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from toon import *

VID = "/tmp/claude-0/-home-user-LifeHacker14/90ebba43-d755-5558-a675-5caff7c9482b/scratchpad/video"
FPS = 30; DUR = 79.15

# ---------- lip sync from narration loudness ----------
w = wave.open(f"{S}/narr.wav"); sr = w.getframerate()
A = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
hop = sr // FPS
RMS = np.array([np.sqrt(np.mean(A[i * hop:(i + 1) * hop] ** 2)) if i * hop < len(A) else 0 for i in range(int(DUR * FPS) + 2)])
RMS = np.clip(RMS / (np.percentile(RMS, 95) + 1e-6), 0, 1)
def mouth(T): return float(RMS[min(len(RMS) - 1, int(T * FPS))]) * (0.6 + 0.4 * abs(math.sin(T * 23)))
def blink(T): return (T % 3.7) < 0.12

# ---------- satellite maps ----------
LAT0 = math.cos(math.radians(50))
SAT = Image.open(f"{S}/sat/eu.jpg").convert("RGB")       # lon -12..42, lat 34..63, equirectangular
SAT = SAT.resize((int(SAT.width * LAT0 * 1.0), SAT.height), Image.LANCZOS)
SAT = ImageEnhance.Color(SAT).enhance(1.15)
LON0, LON1, LATA, LATB = -12, 42, 34, 63
def P(lo, la): return ((lo - LON0) / (LON1 - LON0) * SAT.width, (LATB - la) / (LATB - LATA) * SAT.height)
GEO = {y: json.load(open(f"{S}/data/hb/geojson/world_{y}.geojson"))["features"] for y in (1914, 1920, 1938)}

def polys(year, name):
    for f in GEO[year]:
        if f["properties"].get("NAME") == name:
            g = f["geometry"]; cs = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
            for poly in cs: yield [P(*pt[:2]) for pt in poly[0]]

def sat_map(fills, borders_year=None):
    base = SAT.copy().convert("RGBA"); ov = Image.new("RGBA", base.size, (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
    if borders_year:
        for f in GEO[borders_year]:
            g = f["geometry"]; cs = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
            for poly in cs:
                pts = [P(*pt[:2]) for pt in poly[0]]
                if len(pts) > 2: d.line(pts + [pts[0]], fill=(255, 255, 255, 70), width=2)
    for year, name, col in fills:
        for pts in polys(year, name):
            if len(pts) > 2: d.polygon(pts, fill=col, outline=(255, 255, 255, 200)); d.line(pts + [pts[0]], fill=(255, 255, 255, 200), width=3)
    return Image.alpha_composite(base, ov).convert("RGB")

MAP38 = sat_map([(1938, "Germany", (210, 40, 40, 120))], 1938)
MAP20 = sat_map([(1920, "Germany", (220, 140, 60, 110))], 1920)
MAPLOST = sat_map([(1914, "German Empire", (210, 40, 40, 150)), (1920, "Germany", (240, 200, 120, 150))], None)
MAPPLAIN = sat_map([], 1920)

def cam(img, cx, cy, vw):
    vw = min(vw, img.width, img.height * W / H); vh = vw * H / W
    cx = clamp(cx, vw / 2, img.width - vw / 2); cy = clamp(cy, vh / 2, img.height - vh / 2)
    box = (cx - vw / 2, cy - vh / 2, cx + vw / 2, cy + vh / 2)
    return img.resize((W, H), Image.BICUBIC, box=box), box

def to_screen(box, x, y): sc = W / (box[2] - box[0]); return (x - box[0]) * sc, (y - box[1]) * sc

def map_label(img, xy, s, size, t):
    if t <= 0: return
    d = ImageDraw.Draw(img, "RGBA"); a = int(255 * ease(t * 3))
    d.text(xy, s, font=F(size), fill=(255, 255, 255, a), anchor="mm", stroke_width=3, stroke_fill=(30, 30, 30, a))

def pin(img, x, y, t):
    if t <= 0: return
    d = ImageDraw.Draw(img); a = back(t * 3); yy = y - (1 - ease(t * 3)) * 90
    r = 22 * a
    d.ellipse([x - r, yy - 64 * a, x + r, yy - 20 * a], fill=(240, 196, 40), outline=INK, width=3)
    d.polygon([(x - r * .8, yy - 34 * a), (x + r * .8, yy - 34 * a), (x, yy)], fill=(240, 196, 40), outline=INK)
    d.ellipse([x - 7 * a, yy - 49 * a, x + 7 * a, yy - 35 * a], fill=INK)

def mascot_peek(img, T, x=1720, y=1180, s=.75): mascot(img, x, y, s, mouth=mouth(T), blink=blink(T), look=-1)

# ---------- photos ----------
def photo(p): return ImageEnhance.Contrast(ImageOps.grayscale(Image.open(p)).convert("RGB")).enhance(1.15)
HIMMLER = photo(f"{VID}/img/10.jpg"); BEER = photo(f"{VID}/img/01.jpg")

# ---------- extra scene pieces ----------
def buildings(img, horizon=760):
    d = ImageDraw.Draw(img); cols = [(196, 120, 90), (210, 180, 130), (170, 140, 120), (200, 150, 100), (150, 120, 110)]
    x = -40
    for i in range(9):
        w = 230 + (i * 37) % 80; h = 330 + (i * 53) % 160
        d.rectangle([x, horizon - h, x + w, horizon], fill=cols[i % 5], outline=INK, width=4)
        for r in range(3):
            for c in range(3):
                wx = x + 30 + c * (w - 60) / 3; wy = horizon - h + 40 + r * 90
                if wy < horizon - 70: d.rectangle([wx, wy, wx + 40, wy + 56], fill=(70, 110, 160), outline=INK, width=3)
        x += w - 4
    d.rectangle([0, horizon, W, H], fill=(150, 150, 150)); d.line([0, horizon, W, horizon], fill=INK, width=5)

def podium(img, x, y):
    d = ImageDraw.Draw(img)
    d.polygon([(x - 120, y - 260), (x + 120, y - 260), (x + 90, y), (x - 90, y)], fill=(120, 80, 50), outline=INK, width=5)
    d.rectangle([x - 140, y - 290, x + 140, y - 256], fill=(140, 96, 60), outline=INK, width=5)

def basket(img, x, y, s=1.0, notes=1.0):
    d = ImageDraw.Draw(img)
    for k in range(int(9 * notes)):
        nx = x - 70 * s + (k % 5) * 34 * s; ny = y - 70 * s - (k // 5) * 26 * s
        d.rectangle([nx, ny, nx + 60 * s, ny + 34 * s], fill=(150, 190, 140), outline=INK, width=2)
    d.polygon([(x - 100 * s, y - 50 * s), (x + 100 * s, y - 50 * s), (x + 76 * s, y + 40 * s), (x - 76 * s, y + 40 * s)], fill=(190, 140, 80), outline=INK)
    for k in range(4): d.line([x - 90 * s + k * 0, y - 30 * s + k * 20 * s, x + 90 * s, y - 30 * s + k * 20 * s], fill=INK, width=2)
    d.arc([x - 80 * s, y - 150 * s, x + 80 * s, y + 10 * s], 200, 340, fill=INK, width=int(6 * s))

def counter_text(v): return f"{int(v):,}"

SS = dict(coat=(38, 38, 42), trousers=(28, 28, 32), hat="cap")
SPEAKER = dict(coat=(150, 118, 76), trousers=(80, 66, 50), hair=(50, 34, 24), mustache=True)

# ---------- shots ----------
def s1(img, t, T):
    mascot(img, 330, 1010, 1.05, mouth=mouth(T), blink=blink(T), point=ease(t * 2) * .6)
    hand_text(img, (1150, 470), "the SS", 190, t, cps=8)

def s2(img, t, T):
    mascot(img, 330, 1010, 1.05, mouth=mouth(T), blink=blink(T), point=.4)
    framed(img, HIMMLER, (900, 200, 1300, 720), T - 4.6, "?")
    hand_text(img, (1500, 300), "one", 80, T - 4.7); hand_text(img, (1560, 390), "appointment", 80, T - 4.9)
    badge(img, "1929", T - 5.9)

def s3(img, t, T):
    mascot(img, 260, 1010, .95, mouth=mouth(T), blink=blink(T))
    for i in range(8):
        a = clamp((t - i * .16) * 4)
        if a > 0: person(img, 700 + i * 150, 900 + (1 - back(a)) * 30, .7, alpha=a, **SS)
    hand_text(img, (1220, 200), "a few bodyguards", 84, T - 9.0)

def s4(img, t, T):
    x, y = P(11, 50.5); fr, box = cam(MAP38, x, y, lerp(SAT.width * .95, SAT.width * .75, ease(t / 3.2))); img.paste(fr)
    map_label(img, (W / 2, 150), "the most feared force in Europe", 78, T - 10.3)
    mascot_peek(img, T)

def s5(img, t, T):
    mascot(img, 260, 1010, .95, mouth=mouth(T), blink=blink(T), point=.3)
    framed(img, BEER, (650, 170, 1550, 760), t * 1.2, "Munich, 1920s")
    badge(img, "1925", t)

def s5b(img, t, T):
    img.paste(sky_bg(t=t))
    podium(img, 960, 860)
    person(img, 960, 600, .82, mouth=mouth(T) * .0 + (abs(math.sin(T * 9)) if T > 18.8 else 0), arm=.9 if T > 18.8 else 0, **SPEAKER)
    xs = [560, 680, 800, 1120, 1240, 1360, 440, 1480]
    for i, x in enumerate(xs):
        a = clamp((T - 16.3 - i * .12) * 4)
        if a > 0:
            person(img, x, 930, .66, face=1 if x < 960 else -1, alpha=a, **SS)
            tag(img, (x, 470), str(sorted(xs).index(x) + 1), a)
    hand_text(img, (960, 150), "eight men", 92, T - 16.3)
    hand_text(img, (960, 260), "at Hitler's rallies", 64, T - 19.7)
    badge(img, "1925", 1)

def s6(img, t, T):
    mascot(img, 330, 1010, 1.05, mouth=mouth(T), blink=blink(T))
    hand_text(img, (1150, 460), "20 years later", 130, t, cps=20); badge(img, "1945", t)

def s7(img, t, T):
    mascot(img, 250, 1010, .95, mouth=mouth(T), blink=blink(T), point=.8)
    hand_text(img, (1150, 170), "the SS ran...", 80, t)
    for i, (k, lab, at) in enumerate([("police", "the police", 24.0), ("camp", "the camps", 25.5), ("factory", "companies", 27.5), ("army", "an army", 28.8)]):
        icon(img, k, 640 + i * 340, 560, 1.1, T - at, label=lab)
    badge(img, "1945", 1)

def s8(img, t, T):
    img.paste(room_bg())
    mascot(img, 600, 1000, 1.1, mouth=mouth(T), blink=blink(T), point=.5)
    bubble(img, (760, 360), "Which decision?", T - 33.3, 64)
    d = ImageDraw.Draw(img); q = back((T - 33.6) * 2)
    if q > 0: d.text((1350, 520), "?", font=F(int(420 * q)), fill=RED, anchor="mm")
    hand_text(img, (1350, 870), "...and why it worked", 64, T - 35.3)

def s9(img, t, T):
    img.paste(dusk_bg()); d = ImageDraw.Draw(img)
    for i in range(14):  # skyline silhouette
        x = i * 150; h = 120 + (i * 71) % 220
        d.rectangle([x, 820 - h, x + 130, 820], fill=(30, 26, 36))
        if i % 4 == 1: d.polygon([(x + 40, 820 - h), (x + 65, 820 - h - 120), (x + 90, 820 - h)], fill=(30, 26, 36))
    d.ellipse([1500, 600, 1680, 780], fill=(250, 200, 120))
    hand_text(img, (960, 270), "THE ENTIRE HISTORY OF", 70, t * 1.5, fill=(250, 240, 220), sc=True)
    hand_text(img, (960, 400), "THE SS", 170, t - .5, fill=(250, 240, 220), sc=True, cps=10)
    hand_text(img, (500, 600), "Munich beer hall, 1923", 48, T - 40.6, fill=(250, 240, 220))
    hand_text(img, (1420, 520), "Nuremberg, 1946", 48, T - 42.0, fill=(250, 240, 220))
    mascot(img, 960, 1060, .6, mouth=mouth(T), blink=blink(T))

def s10(img, t, T):
    mx, my = P(11.58, 48.14); cx, cy = P(10.5, 51)
    k = ease(t / 3.4)
    fr, box = cam(MAP20, lerp(cx, mx, k), lerp(cy, my, k), lerp(SAT.width * .5, SAT.width * .3, k)); img.paste(fr)
    sx, sy = to_screen(box, mx, my); pin(img, sx, sy, T - 45.0)
    map_label(img, (sx, sy + 60), "Munich", 64, T - 45.3); badge(img, "1923", 1)
    mascot_peek(img, T)

def s10b(img, t, T):
    img.paste(sky_bg(horizon=760, hills=False)); buildings(img)
    for i in range(3):
        person(img, 420 + i * 150, 1000, .7, coat=(150, 60, 50), hat="flat" if i % 2 else None, face=1, arm=abs(math.sin(T * 6 + i)), mouth=.7)
        person(img, 1500 - i * 150, 1000, .7, coat=(120, 96, 64), face=-1, arm=abs(math.sin(T * 6 + i + 1)), mouth=.7)
    d = ImageDraw.Draw(img)
    for k in range(3):  # little impact stars
        if (T * 3 + k) % 1 < .5: d.text((960 + (k - 1) * 90, 620 + k * 40), "*", font=F(120), fill=(240, 200, 40), anchor="mm")
    hand_text(img, (960, 150), "street fights", 96, T - 48.4); badge(img, "1923", 1)

def s11(img, t, T):
    x, y = P(10.5, 51); fr, box = cam(MAP20, x, y, lerp(SAT.width * .42, SAT.width * .36, ease(t / 6))); img.paste(fr)
    map_label(img, (W / 2, 160), "Germany, 1923", 70, t)
    if T > 56.6:
        d = ImageDraw.Draw(img); a = back((T - 56.6) * 3)
        d.text((W / 2, H / 2), "crisis", font=F(int(220 * a)), fill=RED, anchor="mm", stroke_width=6, stroke_fill=(255, 255, 255))
    badge(img, "1923", 1); mascot_peek(img, T)

def s12(img, t, T):
    mascot(img, 260, 1010, .95, mouth=mouth(T), blink=blink(T))
    person(img, 1300, 960, .85, coat=(110, 116, 96), trousers=(80, 84, 70), hat="helmet", face=-1)
    hand_text(img, (1080, 230), "lost World War One", 100, t); hand_text(img, (1080, 350), "1914 - 1918", 64, t - .6, fill=RED)

def s13(img, t, T):
    x, y = P(14, 51.5); fr, box = cam(MAPLOST, x, y, lerp(SAT.width * .36, SAT.width * .32, ease(t / 3))); img.paste(fr)
    map_label(img, (W / 2, 140), "Treaty of Versailles", 76, t)
    sx, sy = to_screen(box, *P(17.5, 53)); map_label(img, (sx, sy), "lost", 64, T - 62.4)
    badge(img, "1919", 1)

def s14(img, t, T):
    for i in range(10):
        a = clamp((t - i * .05) * 5)
        if a > 0: person(img, 560 + i * 120, 980, .55, coat=(110, 116, 96), trousers=(80, 84, 70), hat="helmet", alpha=a)
    hand_text(img, (960, 170), "army limited to", 70, t)
    d = ImageDraw.Draw(img); d.text((960, 330), counter_text(100000 * ease(t / 1.1)), font=F(150), fill=INK, anchor="mm")

def s15(img, t, T):
    hand_text(img, (360, 260), "Germany", 80, t); hand_text(img, (1560, 260), "France & Britain", 80, t)
    for i in range(4):
        k = clamp((t - i * .35) / 1.2)
        icon(img, "money", lerp(360, 1560, ease(k)), 600 + (i % 2) * 120 - math.sin(k * math.pi) * 120, .9, 1)
    hand_text(img, (960, 950), "reparations", 110, t - .2, fill=RED)

def s16(img, t, T):
    img.paste(room_bg(wall=(222, 214, 196))); d = ImageDraw.Draw(img)
    person(img, 1450, 900, .75, coat=(240, 240, 240), hair=(60, 40, 30), face=-1)
    d.rectangle([1100, 640, 1800, 820], fill=(150, 100, 60), outline=INK, width=5)  # counter in front of the shopkeeper
    icon(img, "bread", 1230, 600, .8, 1)
    person(img, 620, 1000, .8, coat=(90, 100, 130), hat="flat", face=1, arm=.3, mouth=mouth(T) * 0 + (.7 if T > 72.2 else 0))
    basket(img, 820, 960, 1.0)
    d.rounded_rectangle([700, 120, 1700, 330], 18, fill=(40, 40, 44)); d.text((1200, 170), "1 US dollar =", font=F(56), fill=(240, 240, 240), anchor="mm")
    v = 4.2 * 10 ** (12 * ease(t / 5)); d.text((1200, 265), counter_text(v) + " marks", font=F(72 if v < 1e9 else 62), fill=(250, 200, 80), anchor="mm")
    badge(img, "November 1923", 1)
    bubble(img, (560, 400), "My wages!", T - 72.3)

def s17(img, t, T):
    k = ease((T - 75.0) / 3.5)
    top = tuple(int(lerp(a, b, k)) for a, b in zip((120, 180, 230), (60, 50, 90))); bot = tuple(int(lerp(a, b, k)) for a, b in zip((196, 226, 246), (236, 150, 90)))
    img.paste(sky_bg(sky_top=top, sky_bot=bot, hills=True))
    d = ImageDraw.Draw(img); sy = lerp(160, 700, k); d.ellipse([1500, sy, 1640, sy + 140], fill=(250, 220, 90))
    person(img, 760, 980, .85, coat=(90, 100, 130), hat="flat", face=1); basket(img, 960, 940, 1.0)
    hand_text(img, (600, 200), "morning", 80, T - 74.4)
    hand_text(img, (1300, 300), "by evening: worth less", 80, T - 75.9, fill=RED)

SHOTS = [(0, 2.5, s1), (2.5, 7.4, s2), (7.4, 9.7, s3), (9.7, 12.9, s4), (12.9, 16.2, s5), (16.2, 21.5, s5b), (21.5, 22.9, s6),
         (22.9, 30.4, s7), (30.4, 37.1, s8), (37.1, 43.9, s9), (43.9, 47.5, s10), (47.5, 51.9, s10b), (51.9, 57.9, s11),
         (57.9, 60.8, s12), (60.8, 63.6, s13), (63.6, 65.2, s14), (65.2, 67.7, s15), (67.7, 74.3, s16), (74.3, DUR, s17)]

if __name__ == "__main__":
    only = float(sys.argv[1]) if len(sys.argv) > 1 else None
    if only is not None:  # single still for checking
        st, en, fn = next(s for s in SHOTS if s[0] <= only < s[1]); img = grey_bg(); fn(img, only - st, only); img.save(f"{S}/chk/still_{only}.png"); sys.exit()
    p = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                          "-c:v", "libx264", "-preset", "veryfast", "-crf", "19", "-pix_fmt", "yuv420p", f"{S}/c_silent.mp4"], stdin=subprocess.PIPE)
    for fi in range(int(DUR * FPS)):
        T = fi / FPS
        st, en, fn = next((s for s in SHOTS if s[0] <= T < s[1]), SHOTS[-1])
        img = grey_bg(); fn(img, T - st, T)
        p.stdin.write(img.tobytes())
        if fi % 300 == 0: print(f"{T:.0f}s", end=" ", flush=True)
    p.stdin.close(); p.wait()
    cuts = [s[0] for s in SHOTS[1:]]
    wh = ";".join(f"anoisesrc=d=0.3:c=pink:a=0.5,highpass=f=400,lowpass=f=3500,afade=t=in:d=0.12,afade=t=out:st=0.12:d=0.18,adelay={int(c*1000-100)}|{int(c*1000-100)}[w{i}]" for i, c in enumerate(cuts))
    mix = "".join(f"[w{i}]" for i in range(len(cuts)))
    # light, curious pluck-style bed instead of the dark drone (cartoon tone)
    bed = (f"sine=f=261.6:d={DUR}[n1];sine=f=329.6:d={DUR}[n2];sine=f=392:d={DUR}[n3];"
           f"[n1][n2][n3]amix=inputs=3,tremolo=f=2:d=0.9,lowpass=f=1200,volume=0.05[bed]")
    fc = f"{bed};{wh};{mix}amix=inputs={len(cuts)}:normalize=0,volume=0.05[wh];[1:a][bed][wh]amix=inputs=3:duration=first:normalize=0,loudnorm=I=-16:TP=-1.5[out]"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", f"{S}/c_silent.mp4", "-i", f"{S}/narr.wav", "-filter_complex", fc,
                    "-map", "0:v", "-map", "[out]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", f"{S}/cartoon_sample.mp4"], check=True)
    print("\nDONE")
