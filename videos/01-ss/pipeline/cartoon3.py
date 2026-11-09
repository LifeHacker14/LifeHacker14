"""v3: kinetic word-synced text, transitions (slide / circle wipe / zoom), camera drift, screen shake."""
import math, re, subprocess, sys, os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cartoon2 as C2
C = C2.C
from toon import *

FPS = 30; DUR = C2.DUR; NOW = C2.NOW
norm = lambda w: re.sub(r"[^a-z0-9]", "", w.lower())


def wt(word, near_old):
    """new-time at which `word` is spoken, nearest to old-time `near_old`"""
    target = C2.new_of(near_old); best = None
    for w in C2.NEW:
        if norm(w["w"]) == norm(word) and (best is None or abs(w["s"] - target) < abs(best - target)): best = w["s"]
    return best if best is not None else target


def K(img, xy, spec, size=90, **k):
    """spec: list of (display_word, spoken_word_or_None, near_old_time)"""
    items = [(dw, wt(sw, t) if sw else C2.new_of(t)) for dw, sw, t in spec]
    kin(img, xy, items, NOW[0], size, **k)


M = C2.M; walk_in = C2.walk_in


def s1(img, t, T):
    M(img, 340, 1010, 1.05, point=ease(t * 2) * .55, wave_arm=.55 + .25 * math.sin(t * 9) if t < 1.6 else .1, tilt=.4)
    K(img, (1150, 470), [("the", "the", 1.3), ("SS", "SS", 1.5)], 200, hl={"SS": "circle"})

def s2(img, t, T):
    M(img, 340, 1010, 1.05, point=.55 if T > 4.6 else .2, tilt=-.3)
    C.framed(img, C.HIMMLER, (860, 200, 1260, 720), T - 4.6, "?")
    K(img, (1580, 330), [("one", "one", 4.7)], 100)
    K(img, (1580, 450), [("appointment", "appointment", 4.9)], 84, hl={"appointment": "marker"})
    K(img, (1580, 580), [("1929", "1929", 6.0)], 110, hl={"1929": "red"})

def s3(img, t, T):
    M(img, 250, 1010, .95, mood="serious", tilt=.3)
    for i in range(8):
        x, ph = walk_in(t - i * .08, W + 120 + i * 60, 680 + i * 150, 1.1)
        person2(img, x, 930, .72, face=-1, walk=ph, bob=0 if ph else math.sin(NOW[0] * 3 + i) * .3, **C2.SS)
    K(img, (1220, 220), [("a", "a", 8.8), ("few", "few", 9.0), ("bodyguards", "bodyguards", 9.2)], 96, hl={"bodyguards": "underline"})

def s4(img, t, T):
    x, y = C.P(11, 50.5); fr, box = C.cam(C.MAP38, x, y, lerp(C.SAT.width * .95, C.SAT.width * .75, ease(t / 3.2))); img.paste(fr)
    K(img, (W / 2, 150), [("the", "the", 10.1), ("most", "most", 10.4), ("feared", "feared", 10.7), ("force", "force", 11.1), ("in", "in", 11.5), ("Europe", "Europe", 11.7)],
      84, fill=(255, 255, 255), stroke=4, hl={"feared": "red"})
    M(img, 1720, 1180, .75, look=-1, mood="serious")

def s5(img, t, T):
    M(img, 260, 1010, .95, point=.35, tilt=.2)
    C.framed(img, C.BEER, (650, 170, 1550, 760), t * 1.2, "Munich, 1920s")
    badge(img, "1925", t); K(img, (1730, 300), [("1925", "1925", 13.2)], 110, hl={"1925": "red"})

def s5b(img, t, T):
    C2.s5b.__globals__["hand_text"] = lambda *a, **k: None   # silence v2 write-on text in this scene
    C2.s5b(img, t, T)
    K(img, (420, 200), [("8", "eight", 16.3), ("men", "men", 16.6)], 120, hl={"8": "circle"})
    K(img, (420, 320), [("beside", "beside", 18.5), ("Hitler", "Hitler", 19.5)], 70, hl={"Hitler": "marker"})

def s6(img, t, T):
    M(img, 340, 1010, 1.05, wave_arm=.4, tilt=.5)
    d = ImageDraw.Draw(img); k = ease(t / 1.2)
    d.rounded_rectangle([1250, 520, 1650, 900], 24, fill=(255, 255, 255), outline=INK, width=6)
    d.rectangle([1250, 520, 1650, 610], fill=RED, outline=INK, width=6)
    d.text((1450, 760), str(1925 + int(20 * k)), font=F(150), fill=INK, anchor="mm")
    K(img, (1000, 300), [("20", "Twenty", 21.6), ("years", "years", 21.8), ("later", "later", 22.3)], 130, hl={"20": "marker"})
    badge(img, "1945", t)

def s7(img, t, T):
    hits = [24.0, 25.5, 27.5, 28.8]; idx = sum(T > h for h in hits)
    M(img, 250, 1010, .95, point=.35 + .15 * idx, tilt=.3)
    K(img, (1150, 170), [("the", "it", 22.9), ("SS", "it", 22.9), ("ran", "ran", 23.1)], 90, hl={"ran": "underline"})
    for i, (k, lab, at) in enumerate([("police", "the police", 24.0), ("camp", "the camps", 25.5), ("factory", "companies", 27.5), ("army", "an army", 28.8)]):
        icon(img, k, 640 + i * 340, 560 + math.sin(NOW[0] * 2 + i) * 6, 1.1, T - at)
        K(img, (640 + i * 340, 700), [(lab, None, at)], 50)
    badge(img, "1945", 1)

def s8(img, t, T):
    C2.s8.__globals__["hand_text"] = lambda *a, **k: None
    C2.s8(img, t, T)
    K(img, (1350, 870), [("and", "and", 34.9), ("why", "why", 35.5), ("it", "it", 35.7), ("worked", "worked", 35.9)], 70, hl={"worked": "marker"})

def s9(img, t, T):
    img.paste(sky_bg(ground=(40, 34, 44), horizon=820, sky_top=(46, 40, 78), sky_bot=(236, 140, 84), hills=False, clouds=False))
    d = ImageDraw.Draw(img)
    for i in range(14):
        x = i * 150; h = 90 + (i * 71) % 150
        d.rectangle([x, 820 - h, x + 130, 820], fill=(30, 26, 36))
        if i % 4 == 1: d.polygon([(x + 40, 820 - h), (x + 65, 820 - h - 80), (x + 90, 820 - h)], fill=(30, 26, 36))
    d.ellipse([1500, 640, 1660, 800], fill=(250, 200, 120))
    T0 = C2.new_of(37.1)
    kin(img, (960, 230), [(w, T0 + .15 * i) for i, w in enumerate(["THE", "ENTIRE", "HISTORY", "OF"])], NOW[0], 72, fill=(250, 240, 220), sc=True)
    kin(img, (960, 370), [("THE", T0 + .9), ("SS", T0 + 1.1)], NOW[0], 180, fill=(250, 240, 220), sc=True, hl={"SS": "red"})
    K(img, (520, 520), [("Munich", "Munich", 40.6), ("beer", "beer", 40.9), ("hall", "hall", 41.2)], 50, fill=(250, 240, 220))
    K(img, (1420, 520), [("Nuremberg", "Nuremberg", 42.8)], 50, fill=(250, 240, 220), hl={"Nuremberg": "underline"})
    x, ph = walk_in(t, -200, 960, 2.0); M(img, x, 1060, .6)

def s10(img, t, T):
    mx, my = C.P(11.58, 48.14); cx, cy = C.P(10.5, 51); k = ease(t / 3.4)
    fr, box = C.cam(C.MAP20, lerp(cx, mx, k), lerp(cy, my, k), lerp(C.SAT.width * .5, C.SAT.width * .3, k)); img.paste(fr)
    sx, sy = C.to_screen(box, mx, my); C.pin(img, sx, sy, T - 45.0)
    kin(img, (sx, sy + 70), [("Munich", C2.new_of(45.3))], NOW[0], 70, fill=(255, 255, 255), stroke=4)
    badge(img, "1923", 1); M(img, 1720, 1180, .75, look=-1)

def s10b(img, t, T):
    C2.s10b.__globals__["hand_text"] = lambda *a, **k: None
    C2.s10b(img, t, T)
    K(img, (960, 150), [("political", "political", 48.3), ("street", "street", 48.7), ("fights", "fights", 49.3)], 96, hl={"fights": "marker"})

def s11(img, t, T):
    x, y = C.P(10.5, 51); fr, box = C.cam(C.MAP20, x, y, lerp(C.SAT.width * .42, C.SAT.width * .36, ease(t / 6))); img.paste(fr)
    K(img, (W / 2, 160), [("Germany", "Germany", 52.5), ("1923", "1923", 53.3)], 80, fill=(255, 255, 255), stroke=4)
    K(img, (W / 2, H / 2 + 40), [("CRISIS", "crisis", 56.7)], 230, fill=RED, stroke=8, stroke_fill=(255, 255, 255), sc=True)
    badge(img, "1923", 1); M(img, 1720, 1180, .75, look=-1, mood="serious")

def s12(img, t, T):
    C2.s12.__globals__["hand_text"] = lambda *a, **k: None
    C2.s12(img, t, T)
    K(img, (1080, 230), [("lost", "lost", 58.5), ("World", "world", 59.3), ("War", "war", 59.7), ("One", "war", 59.75)], 104, hl={"lost": "red"})
    kin(img, (1080, 360), [("1914 - 1918", C2.new_of(59.9))], NOW[0], 64, fill=RED)

def s13(img, t, T):
    x, y = C.P(14, 51.5); fr, box = C.cam(C.MAPLOST, x, y, lerp(C.SAT.width * .36, C.SAT.width * .32, ease(t / 3))); img.paste(fr)
    K(img, (W / 2, 140), [("Treaty", "Treaty", 60.9), ("of", "of", 61.2), ("Versailles", "Versailles", 61.5)], 80, fill=(255, 255, 255), stroke=4)
    sx, sy = C.to_screen(box, *C.P(17.5, 53)); K(img, (sx, sy), [("taken", "taken", 62.5)], 70, fill=(255, 255, 255), stroke=4)
    badge(img, "1919", 1)

def s14(img, t, T):
    for i in range(10):
        a = clamp((t - i * .05) * 5)
        if a > 0: person2(img, 560 + i * 120, 980, .55, walk=NOW[0] * 2 + i * .1, alpha=a, face=1, **C2.SOLDIER)
    K(img, (960, 170), [("army", "army", 64.3), ("limited", "limited", 63.7), ("to", "limited", 63.8)], 76, hl={"limited": "underline"})
    d = ImageDraw.Draw(img); s = back(t * 2); v = C.counter_text(100000 * ease(t / 1.1))
    if s > 0: d.text((960, 340), v, font=F(int(160 * min(1.15, s))), fill=INK, anchor="mm")

def s15(img, t, T):
    person2(img, 360, 980, .7, face=1, mood="sad", coat=(120, 110, 90)); person2(img, 1560, 980, .7, face=-1, mood="happy", coat=(60, 80, 140))
    K(img, (360, 260), [("Germany", None, 65.3)], 80); K(img, (1560, 260), [("France", None, 65.5), ("&", None, 65.6), ("Britain", None, 65.7)], 70)
    for i in range(4):
        k = clamp((t - i * .35) / 1.2)
        icon(img, "money", lerp(360, 1560, ease(k)), 600 + (i % 2) * 120 - math.sin(k * math.pi) * 120, .9, 1)
    K(img, (960, 950), [("reparations", "reparations", 66.1)], 120, hl={"reparations": "marker"})

def s16(img, t, T): C2.s16(img, t, T)

def s17(img, t, T):
    C2.s17.__globals__["hand_text"] = lambda *a, **k: None
    C2.s17(img, t, T)
    K(img, (600, 200), [("morning", None, 74.4)], 84)
    K(img, (1300, 300), [("by", "by", 75.7), ("evening", "evening", 76.1), ("worth", "worth", 77.5), ("less", "less", 77.8)], 86, hl={"less": "circle"})


FNS = [s1, s2, s3, s4, s5, s5b, s6, s7, s8, s9, s10, s10b, s11, s12, s13, s14, s15, s16, s17]
SHOTS = [(a, b, f) for (a, b, _), f in zip(C2.SHOTS, FNS)]
TRANS = ["slide", "circle", "zoom"]
SHAKES = [C2.new_of(t) for t in (33.6, 56.7)]


def render(tn):
    NOW[0] = tn; T = C2.old_of(tn)
    i = next((k for k, s in enumerate(SHOTS) if s[0] <= T < s[1]), len(SHOTS) - 1)
    st, en, fn = SHOTS[i]; img = grey_bg(); fn(img, T - st, T)
    # gentle camera drift on every shot (Ken Burns)
    k = (tn - C2.new_of(st)) / max(.5, C2.new_of(en) - C2.new_of(st)); z = 1.0 + .035 * k
    img = img.resize((W, H), Image.BILINEAR, box=((W - W / z) / 2 + 12 * k, (H - H / z) / 2, (W + W / z) / 2 + 12 * k, (H + H / z) / 2))
    for s0 in SHAKES: img = shake(img, tn, s0)
    return img, i


if __name__ == "__main__":
    if len(sys.argv) > 1:
        tn = float(sys.argv[1]); render(tn)[0].save(f"{S}/chk/v3_{sys.argv[1]}.png"); sys.exit()
    p = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                          "-c:v", "libx264", "-preset", "veryfast", "-crf", "19", "-pix_fmt", "yuv420p", f"{S}/v3_silent.mp4"], stdin=subprocess.PIPE)
    prev_img, prev_i, trans_start = None, 0, -9
    TD = 0.32
    for fi in range(int(DUR * FPS)):
        tn = fi / FPS; img, i = render(tn)
        if i != prev_i: trans_start = tn; out_img = last; prev_i = i
        if tn - trans_start < TD and i > 0:
            k = ease((tn - trans_start) / TD); kind = TRANS[i % 3]
            if kind == "slide":
                frame = Image.new("RGB", (W, H)); blur = out_img.filter(ImageFilter.BoxBlur(6))
                frame.paste(blur, (int(-W * k), 0)); frame.paste(img.filter(ImageFilter.BoxBlur(int(8 * (1 - k)))), (int(W * (1 - k)), 0)); img = frame
            elif kind == "circle":
                m = Image.new("L", (W, H), 0); r = 1200 * k
                ImageDraw.Draw(m).ellipse([W / 2 - r, H / 2 - r, W / 2 + r, H / 2 + r], fill=255); img = Image.composite(img, out_img, m)
            else:
                z = 1 + .5 * k; zo = out_img.resize((W, H), Image.BILINEAR, box=((W - W / z) / 2, (H - H / z) / 2, (W + W / z) / 2, (H + H / z) / 2))
                img = Image.blend(zo, img, k)
        last = img
        p.stdin.write(img.tobytes())
        if fi % 300 == 0: print(f"{tn:.0f}s", end=" ", flush=True)
    p.stdin.close(); p.wait()
    # audio from v2 mix recipe, with an extra pop for every kinetic word burst is skipped to keep it clean
    ev = [(C2.new_of(c), "whoosh", .4) for c in [s[0] for s in SHOTS[1:]]] + [(C2.new_of(c), "pop", .5) for c in C2.POPS] + \
         [(C2.new_of(c), "ding", .4) for c in C2.DINGS] + [(s0, "pop", .8) for s0 in SHAKES]
    ins = ["-i", f"{S}/v3_silent.mp4", "-i", f"{S}/narr_k.wav", "-i", f"{S}/audio/music.wav"]; fc = []
    for j, (tt, name, g) in enumerate(ev):
        ins += ["-i", f"{S}/audio/sfx_{name}.wav"]; fc.append(f"[{3 + j}:a]adelay={int(tt * 1000)}|{int(tt * 1000)},volume={g}[e{j}]")
    fc.append("[1:a]aresample=44100,pan=stereo|c0=c0|c1=c0,asplit=2[v][vk]")
    fc.append("[2:a]volume=0.32[mu];[mu][vk]sidechaincompress=threshold=0.03:ratio=6:attack=20:release=400[duck]")
    fc.append("".join(f"[e{j}]" for j in range(len(ev))) + f"amix=inputs={len(ev)}:normalize=0[fx]")
    fc.append("[v][duck][fx]amix=inputs=3:duration=first:normalize=0,loudnorm=I=-15:TP=-1.5[out]")
    subprocess.run(["ffmpeg", "-y", "-v", "error", *ins, "-filter_complex", ";".join(fc), "-map", "0:v", "-map", "[out]",
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", f"{S}/cartoon_v3.mp4"], check=True)
    print("\nDONE")
