"""Motion-graphics sample: SS documentary, first ~79 s. Frames are piped straight into ffmpeg."""
import json, math, subprocess, sys, os
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps, ImageEnhance

S = os.path.dirname(os.path.abspath(__file__))
VID = "/tmp/claude-0/-home-user-LifeHacker14/90ebba43-d755-5558-a675-5caff7c9482b/scratchpad/video"
W, H, FPS = 1920, 1080, 30
DUR = 79.15
SERIF = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
SANS = "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"
SANSB = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
BG = (20, 20, 23); CREAM = (238, 232, 220); RED = (196, 30, 36); GREY = (120, 118, 112)
SEA = (17, 24, 33); LAND = (52, 52, 54); BORDER = (82, 82, 86)
_F = {}


def F(p, s):
    if (p, s) not in _F: _F[(p, s)] = ImageFont.truetype(p, s)
    return _F[(p, s)]


def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def ease(x): x = clamp(x); return 1 - (1 - x) ** 3
def lerp(a, b, t): return a + (b - a) * t


# ---------- shared backgrounds ----------
def make_bg():
    g = Image.new("RGB", (W, H), BG)
    n = Image.effect_noise((W, H), 22).convert("RGB")
    g = Image.blend(g, n, 0.05)
    m = Image.new("L", (W, H), 0); ImageDraw.Draw(m).ellipse([-W * .2, -H * .3, W * 1.2, H * 1.3], fill=255)
    return Image.composite(g, Image.new("RGB", (W, H), (6, 6, 8)), m.filter(ImageFilter.GaussianBlur(200)))


BGIMG = make_bg()


# ---------- maps ----------
def load(year):
    return json.load(open(f"{S}/data/hb/geojson/world_{year}.geojson"))["features"]


MAPS = {y: load(y) for y in (1914, 1920, 1938)}
LAT0 = math.cos(math.radians(50))


def map_image(year, lon0, lon1, lat0, lat1, pxw, highlight=None, hl_color=RED, outline_only=None, grey=None):
    pxh = int(pxw * (lat1 - lat0) / ((lon1 - lon0) * LAT0))
    img = Image.new("RGB", (pxw, pxh), SEA); d = ImageDraw.Draw(img)
    P = lambda lo, la: ((lo - lon0) / (lon1 - lon0) * pxw, (lat1 - la) / (lat1 - lat0) * pxh)

    def polys(f):
        g = f["geometry"]; cs = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
        for poly in cs:
            yield [P(*pt[:2]) for pt in poly[0]]

    lw = max(1, pxw // 1600)
    for f in MAPS[year]:
        n = f["properties"].get("NAME")
        col = hl_color if n == highlight else LAND
        for pts in polys(f):
            if len(pts) > 2: d.polygon(pts, fill=col, outline=BORDER, width=lw)
    if grey:  # draw another year's shape on top in a neutral tone (to reveal what was lost)
        for f in MAPS[grey[0]]:
            if f["properties"].get("NAME") == grey[1]:
                for pts in polys(f):
                    d.polygon(pts, fill=(92, 88, 82), outline=(150, 145, 135), width=lw * 2)
    return img, P


def cam(img, cx, cy, vw):
    """crop a W:H window centred at (cx,cy) with width vw (in image px) and scale to 1920x1080"""
    vw = min(vw, img.width, img.height * W / H); vh = vw * H / W
    cx = clamp(cx, vw / 2, img.width - vw / 2); cy = clamp(cy, vh / 2, img.height - vh / 2)
    box = (cx - vw / 2, cy - vh / 2, cx + vw / 2, cy + vh / 2)
    global LAST_BOX; LAST_BOX = box
    return img.resize((W, H), Image.BICUBIC, box=box)


EU, EU_P = map_image(1938, -12, 42, 34, 63, 4200, highlight="Germany")
DE20, DE20_P = map_image(1920, -2, 30, 43, 57, 5200, highlight="Germany", hl_color=(120, 26, 30))
LOST, LOST_P = map_image(1914, -2, 30, 43, 57, 3400, highlight="German Empire", grey=(1920, "Germany"))
MUNICH = (11.58, 48.14)

# ---------- drawing helpers ----------
def text_c(d, xy, s, f, fill, anchor="mm"): d.text(xy, s, font=f, fill=fill, anchor=anchor)


def typed(s, t, cps=22): return s[:int(len(s) * clamp(t * cps / max(1, len(s))))]


def badge(img, year, t):
    if t < 0: return
    d = ImageDraw.Draw(img, "RGBA"); a = int(255 * ease(t * 3))
    f = F(SANSB, 38); w = d.textlength(year, font=f)
    d.rounded_rectangle([56, 48, 56 + w + 44, 112], 10, fill=(0, 0, 0, int(a * .7)))
    d.rectangle([56, 48, 64, 112], fill=RED + (a,))
    d.text((84, 80), year, font=f, fill=CREAM + (a,), anchor="lm")


def pop_text(img, xy, s, f, fill, t, anchor="mm"):
    if t <= 0: return
    a = ease(t * 4); d = ImageDraw.Draw(img, "RGBA")
    dy = (1 - a) * 30
    d.text((xy[0], xy[1] + dy), s, font=f, fill=fill + (int(255 * a),), anchor=anchor)


def label_box(img, xy, s, t, size=46):
    if t <= 0: return
    a = ease(t * 4); d = ImageDraw.Draw(img, "RGBA"); f = F(SANSB, size)
    w = d.textlength(s, font=f); x, y = xy
    d.rectangle([x - 26, y - 34, x + w * a + 26, y + 34], fill=(0, 0, 0, int(190 * a)))
    d.rectangle([x - 26, y - 34, x - 18, y + 34], fill=RED + (int(255 * a),))
    d.text((x, y), s[:max(1, int(len(s) * a))], font=f, fill=CREAM + (int(255 * a),), anchor="lm")


def person(d, x, y, s, fill):
    d.ellipse([x - 18 * s, y - 96 * s, x + 18 * s, y - 60 * s], fill=fill)
    d.rounded_rectangle([x - 30 * s, y - 54 * s, x + 30 * s, y + 40 * s], int(16 * s), fill=fill)


def pin(d, x, y, t):
    if t <= 0: return
    a = ease(t * 3); yy = y - (1 - a) * 80
    d.ellipse([x - 22, yy - 70, x + 22, yy - 26], fill=RED)
    d.polygon([(x - 18, yy - 40), (x + 18, yy - 40), (x, yy)], fill=RED)
    d.ellipse([x - 8, yy - 56, x + 8, yy - 40], fill=CREAM)
    r = 30 + 60 * clamp((t - .3) * 2)
    d.ellipse([x - r, y - r * .45, x + r, y + r * .45], outline=RED + (int(200 * (1 - clamp((t - .3) * 2))),), width=4)


def counter(v): return f"{int(v):,}"


BEER = Image.open(f"{VID}/img/01.jpg").convert("RGB")
BEER = ImageEnhance.Contrast(ImageOps.grayscale(BEER).convert("RGB")).enhance(1.2)
BEER = ImageOps.fit(BEER, (int(W * 1.15), int(H * 1.15)))


# ---------- shots: (start, end, fn(img, t_local, T_abs)) ----------
def s1(img, t, T):
    d = ImageDraw.Draw(img)
    text_c(d, (W / 2, H / 2), typed("THE SS", t, 10), F(SERIF, 220), CREAM)
    tw = d.textlength("THE SS", font=F(SERIF, 220))
    if t > .9: d.rectangle([W / 2 - tw / 2, H / 2 + 120, W / 2 - tw / 2 + tw * ease(t - .9), H / 2 + 130], fill=RED)


def s2(img, t, T):
    d = ImageDraw.Draw(img)
    y = 1900 + 29 * ease(t / 2.4)
    text_c(d, (W / 2, H / 2 - 40), str(int(y)), F(SERIF, 260), RED if y >= 1929 else CREAM)
    pop_text(img, (W / 2, H / 2 + 150), "ONE APPOINTMENT", F(SANSB, 64), CREAM, T - 4.7)


def s3(img, t, T):
    d = ImageDraw.Draw(img)
    for i in range(8):
        ti = t - i * .14
        if ti > 0: person(d, W / 2 - 490 + i * 140, H / 2 + 60 + (1 - ease(ti * 4)) * 40, 1.25, CREAM if i else CREAM)
    pop_text(img, (W / 2, H / 2 + 230), "A FEW BODYGUARDS", F(SANSB, 60), CREAM, T - 9.1)


def s4(img, t, T):
    lo, la = 10.5, 50.5; x, y = EU_P(lo, la)
    frame = cam(EU, x, y, lerp(3600, 3000, ease(t / 3.2)))
    img.paste(frame)
    d = ImageDraw.Draw(img, "RGBA")
    g = int(80 + 60 * math.sin(T * 4))
    d.rectangle([0, 0, W, H], fill=(196, 30, 36, int(40 * clamp(t))))
    pop_text(img, (W / 2, 150), "THE MOST FEARED FORCE IN EUROPE", F(SERIF, 72), CREAM, T - 10.4)


def s5(img, t, T):
    k = ease(t / 3.4); bw = BEER.width - int(lerp(0, 180, k))
    fr = BEER.resize((W, H), Image.BICUBIC, box=(lerp(0, 120, k), lerp(0, 60, k), lerp(0, 120, k) + bw, lerp(0, 60, k) + bw * H / W))
    img.paste(fr); badge(img, "1925", t)
    label_box(img, (150, H - 160), "Munich, 1925", t - .4)


def s5b(img, t, T):
    d = ImageDraw.Draw(img)
    for i in range(8):
        ti = t - i * .1
        if ti > 0: person(d, W / 2 - 420 + i * 120, H / 2 + 40, 1.0, CREAM)
    text_c(d, (W / 2, H / 2 - 170), "8 MEN", F(SERIF, 150), RED)
    pop_text(img, (W / 2, H / 2 + 200), "Bodyguards at Hitler's rallies", F(SANS, 54), CREAM, T - 18.1)
    badge(img, "1925", 1)


def s6(img, t, T):
    d = ImageDraw.Draw(img); k = ease(t / 1.3)
    x0, x1, y = 300, W - 300, H / 2 + 60
    d.line([x0, y, x1, y], fill=GREY, width=6); d.line([x0, y, lerp(x0, x1, k), y], fill=RED, width=10)
    text_c(d, (x0, y + 70), "1925", F(SANSB, 48), CREAM); text_c(d, (x1, y + 70), "1945", F(SANSB, 48), CREAM if k > .95 else GREY)
    text_c(d, (W / 2, H / 2 - 120), f"+{int(20 * k)} YEARS", F(SERIF, 130), CREAM)


def s7(img, t, T):
    badge(img, "1945", 1)
    d = ImageDraw.Draw(img)
    text_c(d, (W / 2, 190), "THE SS NOW RAN", F(SANSB, 56), GREY)
    items = [("THE POLICE", 24.0), ("THE CONCENTRATION CAMPS", 25.5), ("A NETWORK OF COMPANIES", 27.5), ("AN ARMY OF ITS OWN", 28.8)]
    for i, (s, at) in enumerate(items):
        label_box(img, (560, 360 + i * 150), s, T - at, 58)


def s8(img, t, T):
    d = ImageDraw.Draw(img)
    text_c(d, (W / 2, H / 2 - 60), "WHICH DECISION", F(SERIF, 130), CREAM)
    if T > 33.4: d.rectangle([W / 2 - 520, H / 2 + 30, W / 2 - 520 + 1040 * ease((T - 33.4) * 2), H / 2 + 40], fill=RED)
    pop_text(img, (W / 2, H / 2 + 140), "…and why it worked", F(SANS, 64), CREAM, T - 35.4)
    q = int(255 * clamp((t - .3) * 2)); dd = ImageDraw.Draw(img, "RGBA")
    tw = dd.textlength("WHICH DECISION", font=F(SERIF, 130))
    dd.text((W / 2 + tw / 2 + 20, H / 2 - 60), "?", font=F(SERIF, 150), fill=RED + (q,), anchor="lm")


def s9(img, t, T):
    d = ImageDraw.Draw(img)
    text_c(d, (W / 2, 330), "THE ENTIRE HISTORY", F(SERIF, 104), CREAM)
    text_c(d, (W / 2, 470), "OF THE SS", F(SERIF, 150), RED)
    k = ease((T - 38.4) / 4.2); x0, x1, y = 360, W - 360, 720
    d.line([x0, y, x1, y], fill=GREY, width=4); d.line([x0, y, lerp(x0, x1, k), y], fill=RED, width=8)
    pop_text(img, (x0, y + 60), "1923 · Munich beer hall", F(SANS, 40), CREAM, T - 40.6)
    pop_text(img, (x1, y + 60), "1946 · Nuremberg", F(SANS, 40), CREAM, T - 42.0)


def s10(img, t, T):
    k = ease(t / 6.5)
    mx, my = DE20_P(*MUNICH); cx, cy = DE20_P(10.5, 51)
    img.paste(cam(DE20, lerp(cx, mx, k), lerp(cy, my - 250, k), lerp(4200, 1900, k)))
    ox, oy, bx1, _ = LAST_BOX; sc = W / (bx1 - ox)
    sx, sy = (mx - ox) * sc, (my - oy) * sc
    d = ImageDraw.Draw(img, "RGBA"); badge(img, "1923", t)
    pin(d, sx, sy, T - 46.3)
    pop_text(img, (sx + 50, sy - 50), "MUNICH", F(SANSB, 54), CREAM, T - 46.6, anchor="lm")
    pop_text(img, (W / 2, H - 120), "Political street fights: everyday life", F(SANS, 48), CREAM, T - 48.6)


def s11(img, t, T):
    x, y = DE20_P(10.5, 51.2)
    img.paste(cam(DE20, x, y, lerp(3000, 2700, ease(t / 6))))
    badge(img, "1923", 1)
    d = ImageDraw.Draw(img, "RGBA")
    if T > 56.6:
        a = ease((T - 56.6) * 3); s = lerp(1.6, 1.0, a)
        f = F(SERIF, int(200 * s)); d.text((W / 2, H / 2), "CRISIS", font=f, fill=CREAM + (int(255 * a),), anchor="mm", stroke_width=6, stroke_fill=(0, 0, 0, int(200 * a)))


def s12(img, t, T):
    d = ImageDraw.Draw(img)
    text_c(d, (W / 2, H / 2 - 40), typed("LOST THE FIRST WORLD WAR", t, 28), F(SERIF, 100), CREAM)
    pop_text(img, (W / 2, H / 2 + 90), "1914 — 1918", F(SANSB, 56), RED, t - .5)


def s13(img, t, T):
    x, y = LOST_P(13.5, 51.5)
    img.paste(cam(LOST, x, y, lerp(2300, 2100, ease(t / 3))))
    badge(img, "1919", 1)
    pop_text(img, (W / 2, 120), "The Treaty of Versailles", F(SERIF, 72), CREAM, t)
    label_box(img, (130, H - 150), "Red: land Germany lost", T - 62.4, 44)


def s14(img, t, T):
    d = ImageDraw.Draw(img)
    text_c(d, (W / 2, H / 2 - 150), "ARMY LIMITED TO", F(SANSB, 64), GREY)
    text_c(d, (W / 2, H / 2), counter(100000 * ease(t / 1.2)), F(SERIF, 190), CREAM)
    text_c(d, (W / 2, H / 2 + 150), "MEN", F(SANSB, 64), GREY)


def s15(img, t, T):
    d = ImageDraw.Draw(img, "RGBA"); a = ease(t * 3)
    d.text((W / 2, H / 2), "REPARATIONS", font=F(SERIF, int(lerp(220, 150, a))), fill=RED + (int(255 * a),), anchor="mm")


def s16(img, t, T):
    badge(img, "NOVEMBER 1923", 1); d = ImageDraw.Draw(img)
    text_c(d, (W / 2, 300), "1 US DOLLAR =", F(SANSB, 70), GREY)
    v = 4.2 * 10 ** (12 * ease(t / 5.0))
    text_c(d, (W / 2, H / 2 + 20), counter(v), F(SERIF, 150 if v < 1e9 else 120), RED if t > 5 else CREAM)
    text_c(d, (W / 2, H / 2 + 170), "MARKS", F(SANSB, 70), GREY)


def s17(img, t, T):
    d = ImageDraw.Draw(img)
    for i, (lab, val, at) in enumerate([("MORNING", 1.0, 74.4), ("EVENING", 0.25, 75.9)]):
        a = ease((T - at) * 3)
        if a <= 0: continue
        x = W / 2 - 400 + i * 800
        text_c(d, (x, 330), lab, F(SANSB, 60), CREAM)
        h = 380 * val * a
        d.rectangle([x - 90, 820 - h, x + 90, 820], fill=CREAM if i == 0 else RED)
    pop_text(img, (W / 2, 930), "the same wages", F(SANS, 50), GREY, T - 76.6)


SHOTS = [(0, 2.5, s1), (2.5, 7.4, s2), (7.4, 9.7, s3), (9.7, 12.9, s4), (12.9, 16.2, s5), (16.2, 21.5, s5b),
         (21.5, 22.9, s6), (22.9, 30.4, s7), (30.4, 37.1, s8), (37.1, 43.9, s9), (43.9, 51.9, s10), (51.9, 57.9, s11),
         (57.9, 60.8, s12), (60.8, 63.6, s13), (63.6, 65.2, s14), (65.2, 67.7, s15), (67.7, 74.3, s16), (74.3, DUR, s17)]

out = f"{S}/sample_video.mp4"
p = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                      "-c:v", "libx264", "-preset", "veryfast", "-crf", "19", "-pix_fmt", "yuv420p", f"{S}/silent.mp4"], stdin=subprocess.PIPE)
N = int(DUR * FPS)
for fi in range(N):
    T = fi / FPS
    st, en, fn = next(s for s in SHOTS if s[0] <= T < s[1] or s is SHOTS[-1])
    img = BGIMG.copy(); fn(img, T - st, T)
    # gentle push-in on every shot + short dip at cuts
    z = 1 + 0.025 * clamp((T - st) / max(.1, en - st))
    if z > 1: img = img.resize((W, H), Image.BILINEAR, box=((W - W / z) / 2, (H - H / z) / 2, (W + W / z) / 2, (H + H / z) / 2))
    fade = min(clamp((T - st) / .18), clamp((en - T) / .12)) if st > 0 else clamp((en - T) / .12)
    if fade < 1: img = Image.blend(Image.new("RGB", (W, H), (0, 0, 0)), img, .35 + .65 * fade)
    p.stdin.write(img.tobytes())
    if fi % 300 == 0: print(f"{T:.0f}s", end=" ", flush=True)
p.stdin.close(); p.wait()

# audio: narration + quiet drone + soft whoosh at every cut
cuts = [s[0] for s in SHOTS[1:]]
wh = ";".join(f"anoisesrc=d=0.35:c=pink:a=0.5,highpass=f=300,lowpass=f=3000,afade=t=in:d=0.15,afade=t=out:st=0.15:d=0.2,adelay={int(c*1000-120)}|{int(c*1000-120)}[w{i}]" for i, c in enumerate(cuts))
mix = "".join(f"[w{i}]" for i in range(len(cuts)))
drone = f"sine=f=55:d={DUR},volume=0.5[a];sine=f=82.4:d={DUR},volume=0.3[b];[a][b]amix=inputs=2,lowpass=f=400,tremolo=f=0.1:d=0.4,volume=0.10[dr]"
fc = f"{drone};{wh};{mix}amix=inputs={len(cuts)}:normalize=0,volume=0.05[wh];[1:a][dr][wh]amix=inputs=3:duration=first:normalize=0,loudnorm=I=-16:TP=-1.5[out]"
subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", f"{S}/silent.mp4", "-i", f"{S}/narr.wav", "-filter_complex", fc,
                "-map", "0:v", "-map", "[out]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", out], check=True)
print("\nDONE", out)
