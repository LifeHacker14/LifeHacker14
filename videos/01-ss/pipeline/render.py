"""Render the SS documentary: frames -> per-beat clips -> final mp4 + chapters + credits."""
import json, os, subprocess, sys, random
from concurrent.futures import ThreadPoolExecutor
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps, ImageEnhance

sys.path.insert(0, os.path.dirname(__file__))
from plan import PLAN

V = sys.argv[1]
B = f"{V}/build"; os.makedirs(f"{B}/frames", exist_ok=True); os.makedirs(f"{B}/clips", exist_ok=True)
W, H = 1920, 1080
BW, BH = 2112, 1188  # oversize for Ken Burns pans
SERIF = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
SANS = "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"
SANSB = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
RED = (178, 20, 27)
beats = json.load(open(f"{B}/beats.json"))
credits = {int(k): v for k, v in json.load(open(f"{B}/credits.json")).items()} if os.path.exists(f"{B}/credits.json") else {}
SILENT_HOLD = {48: 3.0, 52: 3.0, 70: 12.0}


def font(p, s):
    return ImageFont.truetype(p, s)


def vignette(img):
    m = Image.new("L", img.size, 0)
    d = ImageDraw.Draw(m)
    d.ellipse([-img.width * 0.25, -img.height * 0.35, img.width * 1.25, img.height * 1.35], fill=255)
    m = m.filter(ImageFilter.GaussianBlur(220))
    return Image.composite(img, Image.new("RGB", img.size, (0, 0, 0)), m)


def background():
    g = Image.new("RGB", (BW, BH), (14, 14, 16))
    noise = Image.effect_noise((BW, BH), 18).convert("RGB")
    g = Image.blend(g, noise, 0.06)
    return vignette(g)


def text_center(d, y, s, f, fill):
    w = d.textlength(s, font=f)
    d.text(((BW - w) / 2, y), s, font=f, fill=fill)


def card(lines):
    img = background(); d = ImageDraw.Draw(img)
    big = font(SERIF, 120 if len(lines[0]) < 16 else 92)
    sub = font(SANS, 54)
    hs = [big.size + 30] + [sub.size + 26 for _ in lines[1:]]
    y = (BH - sum(hs)) / 2
    for i, s in enumerate(lines):
        if i == 0:
            text_center(d, y, s, big, (240, 236, 228))
            bottom = d.textbbox((0, y), s, font=big)[3]
            d.rectangle([BW / 2 - 90, bottom + 22, BW / 2 + 90, bottom + 28], fill=RED)
            y = bottom + 60
        else:
            col = (230, 60, 60) if s.isupper() and len(s) > 3 else (200, 196, 188)
            text_center(d, y, s, sub, col)
            y += hs[i]
    return img


def photo(path, caption):
    src = Image.open(path).convert("RGB")
    src = ImageOps.grayscale(src).convert("RGB")
    src = ImageEnhance.Contrast(src).enhance(1.15)
    src = Image.blend(src, Image.new("RGB", src.size, (112, 92, 66)), 0.12)  # light sepia
    bg = ImageOps.fit(src, (BW, BH)).filter(ImageFilter.GaussianBlur(40))
    bg = ImageEnhance.Brightness(bg).enhance(0.45)
    fg = ImageOps.contain(src, (BW, BH))
    bg.paste(fg, ((BW - fg.width) // 2, (BH - fg.height) // 2))
    img = vignette(bg)
    if caption:
        d = ImageDraw.Draw(img, "RGBA")
        f = font(SANSB, 46)
        tw = d.textlength(caption, font=f)
        x, y = 190, BH - 230
        d.rectangle([x - 30, y - 22, x + tw + 30, y + 70], fill=(0, 0, 0, 170))
        d.rectangle([x - 30, y - 22, x - 22, y + 70], fill=RED)
        d.text((x, y), caption, font=f, fill=(240, 236, 228))
    return img


def dur(path):
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path]))


jobs = []
for i, b in enumerate(beats):
    kind = PLAN[i]
    if kind[0] == "photo" and os.path.exists(f"{V}/img/{i:02d}.jpg"):
        frame = photo(f"{V}/img/{i:02d}.jpg", kind[2])
    elif kind[0] == "photo":
        frame = card([kind[2] or b["chapter"]])  # fallback when no licensed photo was found
    else:
        frame = card(kind[1])
    fp = f"{B}/frames/{i:02d}.png"; frame.save(fp)
    a = f"{V}/audio/{i:02d}.wav"
    d = (dur(a) + 0.6) if os.path.exists(a) else 3.5
    d += SILENT_HOLD.get(i, 0)
    jobs.append((i, fp, a if os.path.exists(a) else None, d))

random.seed(7)


def clip(job):
    i, fp, a, d = job
    out = f"{B}/clips/{i:02d}.mp4"
    if os.path.exists(out): return i
    dx, dy = random.choice([(1, 0), (-1, 0), (0, 1), (1, 1), (-1, 1)])
    x = f"(iw-ow)/2+{dx}*(iw-ow)/2*(t/{d:.2f}-0.5)"
    y = f"(ih-oh)/2+{dy}*(ih-oh)/2*(t/{d:.2f}-0.5)"
    vf = f"crop={W}:{H}:'{x}':'{y}',fade=t=in:st=0:d=0.35,fade=t=out:st={d-0.35:.2f}:d=0.35,format=yuv420p"
    cmd = ["ffmpeg", "-y", "-v", "error", "-loop", "1", "-framerate", "30", "-i", fp]
    if a:
        cmd += ["-i", a, "-af", f"adelay=200|200,apad,atrim=0:{d:.2f}"]
    else:
        cmd += ["-f", "lavfi", "-i", f"anullsrc=r=22050:cl=mono", "-af", f"atrim=0:{d:.2f}"]
    cmd += ["-t", f"{d:.2f}", "-vf", vf, "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-r", "30",
            "-c:a", "aac", "-ar", "44100", "-ac", "2", "-b:a", "160k", out]
    subprocess.run(cmd, check=True)
    return i


with ThreadPoolExecutor(4) as ex:
    for i in ex.map(clip, jobs):
        print(i, end=" ", flush=True)

with open(f"{B}/list.txt", "w") as f:
    for i, *_ in jobs:
        f.write(f"file '{B}/clips/{i:02d}.mp4'\n")
total = sum(j[3] for j in jobs)
subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", f"{B}/list.txt", "-c", "copy", f"{B}/voice_only.mp4"], check=True)
# quiet ambient drone underneath the narration
drone = ("sine=f=55:d={t},volume=0.5[a];sine=f=82.4:d={t},volume=0.3[b];sine=f=110:d={t},volume=0.15[c];"
         "[a][b][c]amix=inputs=3,lowpass=f=400,tremolo=f=0.1:d=0.4,afade=t=in:d=4,afade=t=out:st={o}:d=6,volume=0.09").format(t=total, o=total - 6)
subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", f"{B}/voice_only.mp4",
                "-filter_complex", f"{drone}[m];[0:a][m]amix=inputs=2:duration=first:normalize=0,loudnorm=I=-16:TP=-1.5[out]",
                "-map", "0:v", "-map", "[out]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", f"{B}/final.mp4"], check=True)

# chapters + credits
t = 0.0; seen = set(); chapters = []
for (i, _, _, d), b in zip(jobs, beats):
    c = b["chapter"]
    if c not in seen:
        seen.add(c); m, s = divmod(int(t), 60)
        name = c.split(": ", 1)[-1].title() if c.startswith("CHAPTER") else {"HOOK": "Intro", "0:20 THE TURN": "Intro"}.get(c, c.title())
        if not chapters or chapters[-1][1] != name:
            chapters.append((f"{m:02d}:{s:02d}", name))
    t += d
json.dump(dict(total=total, chapters=chapters), open(f"{B}/timing.json", "w"), indent=1)
print("\nTOTAL", round(total / 60, 2), "min")
for c in chapters:
    print(*c)
