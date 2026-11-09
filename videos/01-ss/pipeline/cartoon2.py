"""Cartoon explainer v2: v2 characters with walking/gestures/moods, Kokoro voice, music bed, SFX, time-warped to new narration."""
import json, math, subprocess, sys, wave, os
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cartoon as C
C.mascot = lambda *a, **k: None   # v1 mascot off; v2 draws mascot2
from toon import *

FPS = 30
OLD = json.load(open(f"{S}/words.json")); NEW = json.load(open(f"{S}/words_k.json"))
OT = np.array([0.0] + [w["s"] for w in OLD] + [C.DUR]); NT = np.array([0.0] + [w["s"] for w in NEW] + [NEW[-1]["e"] + 0.9])
DUR = float(NT[-1])
def old_of(tn): return float(np.interp(tn, NT, OT))
def new_of(to): return float(np.interp(to, OT, NT))

# lip sync from the new voice
w = wave.open(f"{S}/nk16.wav"); sr = w.getframerate()
A = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
hop = sr // FPS; NF = int(DUR * FPS) + 2
RMS = np.array([np.sqrt(np.mean(A[i * hop:(i + 1) * hop] ** 2)) if i * hop < len(A) else 0 for i in range(NF)])
RMS = np.clip(RMS / (np.percentile(RMS, 95) + 1e-6), 0, 1)
NOW = [0.0]
def mouth(_=None): return float(RMS[min(NF - 1, int(NOW[0] * FPS))]) * (0.55 + 0.45 * abs(math.sin(NOW[0] * 21)))
def blink(_=None): return (NOW[0] % 3.3) < 0.11
def bob(): return math.sin(NOW[0] * 3.2)

SS = dict(coat=(38, 38, 42), trousers=(28, 28, 32), hat="cap", collar=(60, 60, 64))
SPK = dict(coat=(150, 118, 76), trousers=(80, 66, 50), hair=(50, 34, 24), mustache=True)
WORKER = dict(coat=(90, 100, 130), trousers=(60, 60, 70), hat="flat")
SOLDIER = dict(coat=(110, 116, 96), trousers=(80, 84, 70), hat="helmet", collar=(110, 116, 96))

def M(img, x, y, s=1.0, **k): mascot2(img, x, y, s, mouth=mouth(), blink=blink(), bob=bob(), **k)

def walk_in(t, x0, x1, dur=1.0):
    k = clamp(t / dur); x = lerp(x0, x1, ease(k))
    return x, (abs(x - x0) / 90.0) if k < 1 else None   # (x, walk phase or None when arrived)

def crowd(img, n=14, y=1080):
    d = ImageDraw.Draw(img)
    for i in range(n):
        x = i * 150 + (i % 2) * 40; r = 70 + (i * 13) % 20
        d.ellipse([x - r, y - 120 - (i % 3) * 14, x + r, y + 40], fill=(60 + i * 3 % 30, 52, 50), outline=INK, width=4)

# ---------------- shots (t = local old-time, T = absolute old-time) ----------------
def s1(img, t, T):
    M(img, 340, 1010, 1.05, point=ease(t * 2) * .55, wave_arm=.55 + .25 * math.sin(t * 9) if t < 1.6 else .1, tilt=.4)
    hand_text(img, (1150, 470), "the SS", 190, t, cps=8)

def s2(img, t, T):
    M(img, 340, 1010, 1.05, point=.55 if T > 4.6 else .2, tilt=-.3, look=1)
    C.framed(img, C.HIMMLER, (900, 200, 1300, 720), T - 4.6, "?")
    hand_text(img, (1520, 300), "one", 84, T - 4.7); hand_text(img, (1560, 395), "appointment", 84, T - 4.9)
    badge(img, "1929", T - 5.9)

def s3(img, t, T):
    M(img, 250, 1010, .95, mood="serious", tilt=.3)
    for i in range(8):
        x, ph = walk_in(t - i * .08, W + 120 + i * 60, 680 + i * 150, 1.1)
        person2(img, x, 930, .72, face=-1, walk=ph, bob=0 if ph else math.sin(NOW[0] * 3 + i) * .3, **SS)
    hand_text(img, (1220, 200), "a few bodyguards", 84, T - 9.0)

def s4(img, t, T):
    x, y = C.P(11, 50.5); fr, box = C.cam(C.MAP38, x, y, lerp(C.SAT.width * .95, C.SAT.width * .75, ease(t / 3.2))); img.paste(fr)
    C.map_label(img, (W / 2, 150), "the most feared force in Europe", 78, T - 10.3)
    M(img, 1720, 1180, .75, look=-1, mood="serious")

def s5(img, t, T):
    M(img, 260, 1010, .95, point=.35, tilt=.2)
    C.framed(img, C.BEER, (650, 170, 1550, 760), t * 1.2, "Munich, 1920s"); badge(img, "1925", t)

def s5b(img, t, T):
    img.paste(sky_bg(t=t)); C.podium(img, 960, 860)
    talking = T > 18.6
    person2(img, 960, 610, .85, face=1 if (int(NOW[0] * 1.3) % 2) else -1, arm_r=(.55 + .45 * abs(math.sin(NOW[0] * 4))) if talking else 0,
            mouth=abs(math.sin(NOW[0] * 11)) if talking else 0, mood="angry" if talking else "neutral", **SPK)
    xs = [440, 560, 680, 800, 1120, 1240, 1360, 1480]
    for i, x1 in enumerate(xs):
        x0 = -150 if x1 < 960 else W + 150
        x, ph = walk_in(T - 16.3 - (3 - i if x1 < 960 else i - 4) * .1, x0, x1, 1.0)
        person2(img, x, 930, .66, face=1 if x1 < 960 else -1, walk=ph, **SS)
        if ph is None: tag(img, (x1, 470), str(i + 1), 1)
    crowd(img)
    hand_text(img, (420, 200), "eight men", 92, T - 16.3); hand_text(img, (420, 300), "at Hitler's rallies", 60, T - 19.7)
    badge(img, "1925", 1)

def s6(img, t, T):
    M(img, 340, 1010, 1.05, wave_arm=.4, tilt=.5)
    d = ImageDraw.Draw(img); k = ease(t / 1.2)                       # calendar flipping 1925 -> 1945
    d.rounded_rectangle([1250, 520, 1650, 900], 24, fill=(255, 255, 255), outline=INK, width=6)
    d.rectangle([1250, 520, 1650, 610], fill=RED, outline=INK, width=6)
    d.text((1450, 760), str(1925 + int(20 * k)), font=F(150), fill=INK, anchor="mm")
    hand_text(img, (1000, 300), "20 years later", 120, t, cps=22); badge(img, "1945", t)

def s7(img, t, T):
    hits = [24.0, 25.5, 27.5, 28.8]; idx = sum(T > h for h in hits)
    M(img, 250, 1010, .95, point=.35 + .15 * idx, tilt=.3)
    hand_text(img, (1150, 170), "the SS ran...", 80, t)
    for i, (k, lab, at) in enumerate([("police", "the police", 24.0), ("camp", "the camps", 25.5), ("factory", "companies", 27.5), ("army", "an army", 28.8)]):
        icon(img, k, 640 + i * 340, 560 + math.sin(NOW[0] * 2 + i) * 6, 1.1, T - at, label=lab)
    badge(img, "1945", 1)

def s8(img, t, T):
    img.paste(room_bg()); surprised = T > 33.5
    M(img, 600, 1000, 1.1, point=.9 if surprised else .5, wave_arm=.85 if surprised else .1, mood="surprised" if surprised else "happy")
    bubble(img, (760, 350), "Which decision?", T - 33.3, 64)
    d = ImageDraw.Draw(img); q = back((T - 33.6) * 2)
    if q > 0: d.text((1350, 520 + math.sin(NOW[0] * 5) * 10), "?", font=F(int(420 * q)), fill=RED, anchor="mm")
    hand_text(img, (1350, 870), "...and why it worked", 64, T - 35.3)

def s9(img, t, T):
    img.paste(sky_bg(ground=(40, 34, 44), horizon=820, sky_top=(46, 40, 78), sky_bot=(236, 140, 84), hills=False, clouds=False))
    d = ImageDraw.Draw(img)
    for i in range(14):  # lower skyline so it never touches the title
        x = i * 150; h = 90 + (i * 71) % 150
        d.rectangle([x, 820 - h, x + 130, 820], fill=(30, 26, 36))
        if i % 4 == 1: d.polygon([(x + 40, 820 - h), (x + 65, 820 - h - 80), (x + 90, 820 - h)], fill=(30, 26, 36))
    d.ellipse([1500, 640, 1660, 800], fill=(250, 200, 120))
    hand_text(img, (960, 230), "THE ENTIRE HISTORY OF", 70, t * 1.5, fill=(250, 240, 220), sc=True)
    hand_text(img, (960, 360), "THE SS", 170, t - .5, fill=(250, 240, 220), sc=True, cps=10)
    hand_text(img, (520, 520), "Munich beer hall, 1923", 46, T - 40.6, fill=(250, 240, 220))
    hand_text(img, (1420, 520), "Nuremberg, 1946", 46, T - 42.0, fill=(250, 240, 220))
    x, ph = walk_in(t, -200, 960, 2.0)
    M(img, x, 1060, .6)

def s10(img, t, T):
    mx, my = C.P(11.58, 48.14); cx, cy = C.P(10.5, 51); k = ease(t / 3.4)
    fr, box = C.cam(C.MAP20, lerp(cx, mx, k), lerp(cy, my, k), lerp(C.SAT.width * .5, C.SAT.width * .3, k)); img.paste(fr)
    sx, sy = C.to_screen(box, mx, my); C.pin(img, sx, sy, T - 45.0)
    C.map_label(img, (sx, sy + 60), "Munich", 64, T - 45.3); badge(img, "1923", 1)
    M(img, 1720, 1180, .75, look=-1)

def s10b(img, t, T):
    img.paste(sky_bg(horizon=760, hills=False)); C.buildings(img)
    lunge = math.sin(NOW[0] * 5) * 30
    for i in range(3):
        person2(img, 470 + i * 140 + lunge, 1000, .72, coat=(150, 60, 50), hat="flat" if i % 2 else None, face=1,
                arm_r=abs(math.sin(NOW[0] * 7 + i)), mood="angry", mouth=.6, walk=NOW[0] * 1.5 + i * .3)
        person2(img, 1450 - i * 140 - lunge, 1000, .72, coat=(120, 96, 64), face=-1,
                arm_r=abs(math.sin(NOW[0] * 7 + i + 1)), mood="angry", mouth=.6, walk=NOW[0] * 1.5 + i * .3 + .5)
    d = ImageDraw.Draw(img, "RGBA")
    for k in range(6):  # dust cloud in the middle
        r = 60 + 20 * math.sin(NOW[0] * 6 + k)
        d.ellipse([960 - 140 + k * 50 - r, 800 - r + (k % 2) * 30, 960 - 140 + k * 50 + r, 800 + r + (k % 2) * 30], fill=(200, 190, 170, 170))
    for k in range(3):
        if (NOW[0] * 3 + k) % 1 < .5: d.text((960 + (k - 1) * 110, 640 + k * 40), "*", font=F(130), fill=(240, 200, 40), anchor="mm")
    hand_text(img, (960, 150), "street fights", 96, T - 48.4); badge(img, "1923", 1)

def s11(img, t, T):
    C.s11(img, t, T)
    M(img, 1720, 1180, .75, look=-1, mood="serious")

def s12(img, t, T):
    M(img, 260, 1010, .95, mood="serious")
    x, ph = walk_in(t, W + 150, 1300, 2.2)
    person2(img, x, 960, .85, face=-1, walk=ph, mood="sad", tilt=.6, **SOLDIER)
    hand_text(img, (1080, 230), "lost World War One", 100, t); hand_text(img, (1080, 350), "1914 - 1918", 64, t - .6, fill=RED)

def s13(img, t, T): C.s13(img, t, T)

def s14(img, t, T):
    for i in range(10):
        a = clamp((t - i * .05) * 5)
        if a > 0: person2(img, 560 + i * 120, 980, .55, walk=NOW[0] * 2 + i * .1, alpha=a, face=1, **SOLDIER)
    hand_text(img, (960, 170), "army limited to", 70, t)
    d = ImageDraw.Draw(img); d.text((960, 330), C.counter_text(100000 * ease(t / 1.1)), font=F(150), fill=INK, anchor="mm")

def s15(img, t, T):
    person2(img, 360, 980, .7, face=1, mood="sad", coat=(120, 110, 90)); person2(img, 1560, 980, .7, face=-1, mood="happy", coat=(60, 80, 140))
    C.s15(img, t, T)

def s16(img, t, T):
    img.paste(room_bg(wall=(222, 214, 196))); d = ImageDraw.Draw(img)
    shocked = t > 3.5
    person2(img, 1450, 790, .75, coat=(240, 240, 240), hair=(60, 40, 30), face=-1, mood="surprised" if shocked else "neutral", arm_r=.7 if shocked else 0, collar=(250, 250, 250))
    d.rectangle([1100, 640, 1800, 820], fill=(150, 100, 60), outline=INK, width=5)
    icon(img, "bread", 1230, 600, .8, 1)
    x, ph = walk_in(t, -200, 620, 1.6)
    person2(img, x, 1000, .8, face=1, walk=ph, arm_r=.35, mood="sad" if T > 72.2 else "neutral", mouth=.7 if 72.2 < T < 73.5 else 0, **WORKER)
    C.basket(img, x + 200, 960, 1.0)
    d.rounded_rectangle([700, 120, 1700, 330], 18, fill=(40, 40, 44)); d.text((1200, 170), "1 US dollar =", font=F(56), fill=(240, 240, 240), anchor="mm")
    v = 4.2 * 10 ** (12 * ease(t / 5)); d.text((1200, 265), C.counter_text(v) + " marks", font=F(72 if v < 1e9 else 62), fill=(250, 200, 80), anchor="mm")
    badge(img, "November 1923", 1); bubble(img, (560, 400), "My wages!", T - 72.3)

def s17(img, t, T):
    k = ease((T - 75.0) / 3.5)
    top = tuple(int(lerp(a, b, k)) for a, b in zip((120, 180, 230), (60, 50, 90))); bot = tuple(int(lerp(a, b, k)) for a, b in zip((196, 226, 246), (236, 150, 90)))
    img.paste(sky_bg(sky_top=top, sky_bot=bot, hills=True))
    d = ImageDraw.Draw(img); sy = lerp(160, 700, k); d.ellipse([1500, sy, 1640, sy + 140], fill=(250, 220, 90))
    person2(img, 760, 980, .85, face=1, mood="sad" if k > .5 else "neutral", arm_r=.35, **WORKER); C.basket(img, 960, 940, 1.0, notes=lerp(1, .35, k))
    hand_text(img, (600, 200), "morning", 80, T - 74.4); hand_text(img, (1300, 300), "by evening: worth less", 80, T - 75.9, fill=RED)

OLDSHOTS = [s[:2] for s in C.SHOTS]
FNS = [s1, s2, s3, s4, s5, s5b, s6, s7, s8, s9, s10, s10b, s11, s12, s13, s14, s15, s16, s17]
SHOTS = [(a, b, f) for (a, b), f in zip(OLDSHOTS, FNS)]

# SFX events in OLD time
POPS = [4.6, 5.9, 9.0, 16.3, 24.0, 25.5, 27.5, 28.8, 33.3, 33.6, 45.0, 72.3]
DINGS = [6.0, 22.8, 64.7]

if __name__ == "__main__":
    if len(sys.argv) > 1:
        tn = float(sys.argv[1]); NOW[0] = tn; T = old_of(tn); st, en, fn = next(s for s in SHOTS if s[0] <= T < s[1])
        img = grey_bg(); fn(img, T - st, T); img.save(f"{S}/chk/v2_{sys.argv[1]}.png"); sys.exit()
    p = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                          "-c:v", "libx264", "-preset", "veryfast", "-crf", "19", "-pix_fmt", "yuv420p", f"{S}/v2_silent.mp4"], stdin=subprocess.PIPE)
    for fi in range(int(DUR * FPS)):
        tn = fi / FPS; NOW[0] = tn; T = old_of(tn)
        st, en, fn = next((s for s in SHOTS if s[0] <= T < s[1]), SHOTS[-1])
        img = grey_bg(); fn(img, T - st, T)
        k = (tn - new_of(st))                                    # punch-in on every new shot
        if st > 0 and k < .25:
            z = 1 + .06 * (1 - ease(k / .25)); img = img.resize((W, H), Image.BILINEAR, box=((W - W / z) / 2, (H - H / z) / 2, (W + W / z) / 2, (H + H / z) / 2))
        p.stdin.write(img.tobytes())
        if fi % 300 == 0: print(f"{tn:.0f}s", end=" ", flush=True)
    p.stdin.close(); p.wait()
    # audio: voice + music (ducked) + SFX
    ev = [(new_of(c), "whoosh", .35) for c in [s[0] for s in SHOTS[1:]]] + [(new_of(c), "pop", .5) for c in POPS] + [(new_of(c), "ding", .4) for c in DINGS]
    ins = ["-i", f"{S}/v2_silent.mp4", "-i", f"{S}/narr_k.wav", "-i", f"{S}/audio/music.wav"]
    fc = []
    for i, (tt, name, g) in enumerate(ev):
        ins += ["-i", f"{S}/audio/sfx_{name}.wav"]
        fc.append(f"[{3 + i}:a]adelay={int(tt * 1000)}|{int(tt * 1000)},volume={g}[e{i}]")
    fc.append(f"[1:a]aresample=44100,pan=stereo|c0=c0|c1=c0,asplit=2[v][vk]")
    fc.append(f"[2:a]volume=0.32[mu];[mu][vk]sidechaincompress=threshold=0.03:ratio=6:attack=20:release=400[duck]")
    fc.append("".join(f"[e{i}]" for i in range(len(ev))) + f"amix=inputs={len(ev)}:normalize=0[fx]")
    fc.append("[v][duck][fx]amix=inputs=3:duration=first:normalize=0,loudnorm=I=-15:TP=-1.5[out]")
    subprocess.run(["ffmpeg", "-y", "-v", "error", *ins, "-filter_complex", ";".join(fc), "-map", "0:v", "-map", "[out]",
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", f"{S}/cartoon_v2.mp4"], check=True)
    print("\nDONE")
