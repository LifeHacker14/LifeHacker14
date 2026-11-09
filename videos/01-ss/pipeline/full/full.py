"""Full SS video renderer: timeline from Kokoro VO + Whisper word times, per-sentence shots, templates, transitions, audio mix.
usage: full.py prep | full.py still <t> | full.py seg <k> <n> | full.py audio | full.py concat <n>"""
import json, math, os, re, subprocess, sys, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
FULL = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, FULL)
from scenes import *

FPS = 30
BEATS = json.load(open(f"{VID}/build/beats.json"))
norm = lambda w: re.sub(r"[^a-z0-9]", "", w.lower())
NUMW = {"eight", "twenty", "fifty", "thousand", "thousands", "million", "millions", "hundred", "hundreds", "three", "six", "two", "four"}
STOPCAP = {"The", "It", "In", "He", "His", "This", "That", "And", "But", "By", "On", "At", "A", "As", "For", "From", "To", "Over", "Days", "After",
           "Some", "Many", "Others", "Its", "Their", "Then", "Under", "Behind", "Around", "Alongside", "Together", "All", "Who", "When", "Released",
           "Think", "Being", "Officially", "Candidates", "Political", "Rival", "So", "Into", "One", "Within", "Thousands", "Himself", "Here", "Most",
           "Police", "Ideology", "Loyalty", "Organisation", "Organization", "Germany's", "If", "Mass", "Murder", "Officers", "Its", "Of", "They", "We", "You"}
SOLEMN = {42, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 57, 58}

# ======================= scene specs per beat: list of (template, params) cycled over sentences =======================
E = lambda **k: k
SPEC = {
 0: [("mascot", E(kw=["bodyguards", "feared"]))],
 1: [("rally", E(speaker="hitler")), ("icons", E(icons=[("police", "police", "police"), ("camp", "camps", "camps"), ("factory", "companies", "companies"), ("army", "army", "army")])), ("mascot", E(kw=["decision"]))],
 2: [("title", E()), ("map", E(view=(11.5, 48.2, .55, .3), fills=[(1920, "Germany", (220, 140, 60, 110))], year=1920, pins=[(11.58, 48.14, "Munich", "Munich")]))],
 3: [("map", E(view=(10.5, 51, .45, .38), fills=[(1920, "Germany", (220, 140, 60, 110))], year=1920)), ("lostwar", E()),
     ("map", E(view=(14, 51.5, .36, .32), fills=[(1914, "German Empire", (210, 40, 40, 150)), (1920, "Germany", (240, 200, 120, 150))], year=None, kw=["land", "army", "reparations"])),
     ("shop", E())],
 4: [("street", E(mode="crowd")), ("rally", E(speaker="hitler", indoor=True, guards=0))],
 5: [("street", E(mode="fight")), ("march", E(who="sa", kw=["brownshirts"])), ("march", E(who="sa", kw=["control"])), ("rally", E(speaker="hitler", guards=4, kw=["loyal", "personally"]))],
 6: [("date", E(date="1923")), ("march", E(who="ss", kw=["putsch", "force"]))],
 7: [("street", E(mode="police")), ("prison", E(kw=["prison"])), ("mascot", E(kw=["banned", "dissolved"])), ("mascot", E(kw=["end"]))],
 8: [("prison", E(writing=True)), ("mascot", E(kw=["elections"])), ("date", E(date="1925")), ("mascot", E(kw=["nobody"]))],
 9: [("eight", E()), ("org", E(boxes=[("NSDAP", None, 960, 260), ("SA", "SA", 700, 560), ("SS", "SS", 1220, 560)], links=[(0, 1), (0, 2)], tiny=2)), ("mascot", E(kw=["ignored"])), ("mascot", E(kw=["man"]))],
 10: [("photo", E(photo="himmler")), ("date", E(date="1900")), ("farm", E(kw=["agriculture"])), ("farm", E(kw=["poultry", "farm"]))],
 11: [("icons", E(icons=[("scroll", "loyal", "loyal"), ("eye", "ideas", "racial"), ("files", "organiser", "organiser")], kw=["three"])), ("mascot", E(kw=["mystical"])), ("files", E())],
 12: [("date", E(date="6 Jan\n1929"))],
 13: [("mascot", E(kw=["appointment"])), ("counter", E(value=280, label="SS members")), ("org", E(boxes=[("BODYGUARD", None, 960, 380), ("ORDER", "order", 960, 660)], links=[(0, 1)], cross=0))],
 14: [("room", E(people=["official", "ss"], kw=["measured", "photographed"])), ("files", E(kw=["ancestry"])), ("date", E(date="1931", kw=["marry"]))],
 15: [("mascot", E(kw=["strange"])), ("mascot", E(kw=["status"])), ("march", E(who="ss", kw=["chosen"])), ("mascot", E(kw=["command"]))],
 16: [("counter", E(value=50000, label="SS members, 1933", prefix="more than "))],
 17: [("counter", E(value=50000, label="1929: about 280", prefix=""))],
 18: [("room", E(people=["himmler", "heydrich"], desk=True)), ("mascot", E(kw=["navy"])), ("files", E(kw=["plan"])), ("room", E(people=["himmler", "heydrich"], desk=True, kw=["minutes", "job"]))],
 19: [("files", E(kw=["SD"])), ("files", E(kw=["enemies", "party"]))],
 20: [("duo", E()), ("duo", E(kw=["vision", "efficiency"])), ("mascot", E(kw=["machine"]))],
 21: [("duo", E(caption="Vision + Machine"))],
 22: [("date", E(date="30 Jan\n1933")), ("fire", E()), ("mascot", E(kw=["arrest", "trial"]))],
 23: [("map", E(view=(11.5, 48.2, .3, .22), fills=[(1938, "Germany", (220, 140, 60, 90))], year=1938, pins=[(11.43, 48.26, "Dachau", "Dachau")]))],
 24: [("camp", E()), ("camp", E(kw=["communists", "democrats", "unionists"]))],
 25: [("room", E(people=["eicke"], kw=["Eicke"])), ("camp", E(kw=["discipline"])), ("org", E(boxes=[("DACHAU", None, 960, 300), ("camp", None, 500, 650), ("camp", None, 960, 700), ("camp", None, 1420, 650)], links=[(0, 1), (0, 2), (0, 3)], kw=["model"])), ("march", E(who="ss", kw=["Death's", "Head"]))],
 26: [("mascot", E(kw=["guarding"])), ("mascot", E(kw=["removed"], mood="serious"))],
 27: [("mascot", E(kw=["SA"])), ("march", E(who="sa", kw=["millions"])), ("room", E(people=["rohm"], kw=["army"])), ("room", E(people=["official", "soldier"], kw=["horrified", "nervous"]))],
 28: [("mascot", E(kw=["choice"])), ("date", E(date="30 June\n1934"))],
 29: [("street", E(mode="night")), ("street", E(mode="night", kw=["trial"])), ("mascot", E(kw=["rivals"], mood="serious")), ("prison", E(kw=["cell"]))],
 30: [("mascot", E(kw=["Long", "Knives"], mood="serious")), ("date", E(date="20 July\n1934")), ("org", E(boxes=[("HITLER", None, 960, 260), ("SS", "independent", 1260, 600), ("SA", None, 660, 600)], links=[(0, 1)]))],
 31: [("org", E(boxes=[("HITLER", None, 960, 260), ("SS", None, 960, 600)], links=[(0, 1)]))],
 32: [("hq", E()), ("hq", E(kw=["Gestapo"]))],
 33: [("map", E(view=(10.5, 51, .45, .4), fills=[(1938, "Germany", (40, 40, 44, 150))], year=1938, kw=["Himmler", "Heydrich"])), ("date", E(date="17 June\n1936"))],
 34: [("mascot", E(kw=["meant"])), ("mascot", E(kw=["police", "country"])), ("flow", E())],
 35: [("flow", E())],
 36: [("castle", E())],
 37: [("icons", E(icons=[("ring", "rings", "rings"), ("scroll", "ceremonies", "ceremonies"), ("castle", "legends", "knights")])), ("expedition", E()), ("mascot", E(kw=["pseudoscience"]))],
 38: [("mascot", E(kw=["Lebensborn"])), ("mascot", E(kw=["kidnapping"], mood="serious"))],
 39: [("mascot", E(kw=["bizarre"])), ("mascot", E(kw=["historic"])), ("mascot", E(kw=["terrible"], mood="serious"))],
 40: [("march", E(who="ss", kw=["armed"])), ("rally", E(speaker="hitler", guards=8, kw=["Leibstandarte"])), ("march", E(who="ss", kw=["Waffen-SS"]))],
 41: [("org", E(boxes=[("SS-VT", None, 960, 300), ("WAFFEN-SS", None, 960, 650)], links=[(0, 1)]))],
 42: [("street", E(mode="broken")), ("solemn", E())],
 43: [("map", E(view=(19, 52, .5, .42), fills=[(1938, "Poland", (210, 40, 40, 120))], year=1938)), ("org", E(boxes=[("GESTAPO", None, 500, 330), ("KRIPO", None, 960, 330), ("SD", None, 1420, 330), ("RSHA", "RSHA", 960, 700)], links=[(0, 3), (1, 3), (2, 3)]))],
 44: [("org", E(boxes=[("GESTAPO", None, 500, 330), ("KRIPO", None, 960, 330), ("SD", None, 1420, 330), ("RSHA", None, 960, 700)], links=[(0, 3), (1, 3), (2, 3)]))],
 45: [("solemn", E(map=(19, 52, .5), marks=[(21, 52.2), (19.9, 50.06), (17, 51.1), (22.5, 51.2), (18.6, 53.0)]))],
 46: [("solemn", E(map=(26, 52, .75), marks=[(25.3, 54.7), (27.6, 53.9), (30.5, 50.45), (24.0, 49.8), (28.5, 49.2), (33, 51.5)]))],
 47: [("solemn", E(text=["Babi Yar", "29-30 September 1941"]))],
 48: [("solemn", E(map=(26, 51, .75), marks=[(30.5, 50.45), (27.6, 53.9), (25.3, 54.7), (24.0, 49.8), (28.5, 49.2)])), ("solemn", E())],
 49: [("solemn", E(map=(13.15, 52.43, .25), marks=[(13.15, 52.43)])), ("solemn", E())],
 50: [("solemn", E(map=(21, 51, .45), marks=[(23.46, 50.37), (23.6, 51.45), (22.05, 52.63), (19.2, 50.03)], labels=["Belzec", "Sobibor", "Treblinka", "Auschwitz"]))],
 51: [("solemn", E(text=["Six million Jews.", "Millions of others."]))],
 52: [("solemn", E(map=(14.4, 50.1, .3), marks=[(14.42, 50.09), (14.17, 50.15)], labels=["Prague", "Lidice"]))],
 53: [("solemn", E(map=(14.4, 50.1, .25), marks=[(14.17, 50.15)], labels=["Lidice"]))],
 54: [("solemn", E(kw=["empire"])), ("solemn", E(kw=["quarries", "brickworks"])), ("solemn", E(kw=["slave", "labour"]))],
 55: [("solemn", E())],
 56: [("march", E(who="ss", kw=["hundreds"])), ("map", E(view=(12, 50, .9, .85), fills=[(1938, "Germany", (40, 40, 44, 140))], year=1938, kw=["Europe"]))],
 57: [("solemn", E(kw=["soldiers"])), ("solemn", E(map=(3, 48, .6), marks=[(1.03, 45.93), (6.03, 50.43)], labels=["Oradour-sur-Glane", "Malmedy"]))],
 58: [("ruins", E(solemn=True, text=["Oradour-sur-Glane", "as it stands today"]))],
 59: [("ruins", E(who=[])), ("room", E(people=["himmler", "bernadotte"], kw=["Bernadotte"]))],
 60: [("bunker", E()), ("bunker", E(kw=["life"]))],
 61: [("escape", E()), ("escape", E(caught=True)), ("date", E(date="23 May\n1945"))],
 62: [("mascot", E(kw=["crimes"], mood="serious"))],
 63: [("court", E())],
 64: [("court", E(kw=["tried"])), ("map", E(view=(-10, 4, 1.0, 1.0), base="world", fills=[], year=None, route=[(11.5, 48.1), (-58.4, -34.6), (35.2, 31.8)], pins=[(-58.4, -34.6, "Argentina", "Argentina"), (35.2, 31.8, "Jerusalem", "Jerusalem")]))],
 65: [("map", E(view=(-10, 4, 1.0, 1.0), base="world", fills=[], year=None, route=[(11.5, 48.1), (-58.4, -34.6), (35.2, 31.8)]))],
 66: [("eight", E()), ("mascot", E(kw=["uniforms"])), ("date", E(date="6 Jan\n1929")), ("mascot", E(kw=["Himmler"]))],
 67: [("icons", E(icons=[("scroll", "loyalty", "loyalty"), ("eye", "ideology", "ideology"), ("files", "organisation", "organisation")])), ("mascot", E(kw=["willing"])), ("org", E(stack=True))],
 68: [("org", E(stack=True))],
 69: [("end", E())], 70: [("end", E())],
}

# ======================= timeline =======================
def wav_len(p):
    w = wave.open(p); return w.getnframes() / w.getframerate()

def prep():
    from faster_whisper import WhisperModel
    m = WhisperModel("base.en", device="cpu", compute_type="int8")
    tl = []; t = 1.0; last_ch = None
    for i, b in enumerate(BEATS):
        ch = b["chapter"]
        if ch != last_ch and i > 2:
            tl.append(dict(kind="chapter", title=ch, start=t, dur=2.6)); t += 2.6
        last_ch = ch
        p = f"{FULL}/vo/{i:02d}.wav"
        if os.path.exists(p):
            d = wav_len(p)
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", p, "-ar", "16000", "-ac", "1", "/tmp/_w16.wav"], check=True)
            w = wave.open("/tmp/_w16.wav"); a = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
            segs, _ = m.transcribe(a, word_timestamps=True)
            words = [dict(w=x.word.strip(), s=round(t + x.start, 3), e=round(t + x.end, 3)) for s in segs for x in s.words]
            hold = {47: 3.0, 51: 3.0}.get(i, 0)
            tl.append(dict(kind="beat", i=i, start=t, dur=d + hold, audio=p, words=words)); t += d + hold + 0.45
        else:
            d = {70: 12.0}.get(i, 3.2)
            tl.append(dict(kind="beat", i=i, start=t, dur=d, audio=None, words=[])); t += d + 0.3
        print(i, round(t, 1), flush=True)
    json.dump(dict(total=t + 1.0, items=tl), open(f"{FULL}/timeline.json", "w"), indent=0)

# ======================= shots =======================
class Shot: pass

def sentences(words):
    out, cur = [], []
    for w in words:
        cur.append(w)
        if re.search(r"[.?!]$", w["w"]): out.append(cur); cur = []
    if cur: out.append(cur)
    res = []  # split long sentences at commas
    for s in out:
        if s[-1]["e"] - s[0]["s"] > 7.0:
            cut = None
            for k, w in enumerate(s[:-3]):
                if k > 3 and w["w"].endswith(",") and (cut is None or abs(w["e"] - (s[0]["s"] + s[-1]["e"]) / 2) < abs(s[cut]["e"] - (s[0]["s"] + s[-1]["e"]) / 2)): cut = k
            if cut is None: cut = len(s) // 2
            res += [s[:cut + 1], s[cut + 1:]]
        else: res.append(s)
    return res

def keywords(ws, extra):
    extra = {norm(x) for x in extra}; sel = []
    for k, w in enumerate(ws):
        raw = w["w"].strip(",.;:!?\"'()"); n = norm(raw)
        is_num = bool(re.match(r"^\d[\d,]*$", raw)) or n in NUMW and n != "one"
        is_cap = raw[:1].isupper() and raw not in STOPCAP and (k > 0 or n in extra)
        sel.append(bool(raw) and (is_num or is_cap or n in extra))
    chunks, cur = [], []
    for k, (w, s) in enumerate(zip(ws, sel)):
        raw = w["w"].strip(",.;:!?\"")
        if s: cur.append((raw, w["s"]))
        elif cur and norm(raw) in ("of", "the") and k + 1 < len(ws) and sel[k + 1]: cur.append((raw, w["s"]))
        else:
            if cur: chunks.append(cur); cur = []
    if cur: chunks.append(cur)
    chunks = [c for c in chunks if not (len(c) == 1 and norm(c[0][0]) in ("the", "of"))]
    capped = []
    for c in chunks:
        while c and norm(c[-1][0]) in ("the", "of"): c = c[:-1]
        for s0 in range(0, len(c), 4): capped.append(c[s0:s0 + 4])
    chunks = [c for c in capped if c]
    if len(chunks) > 3:
        score = lambda c: sum(len(x[0]) for x in c) + (6 if any(x[0][:1].isdigit() for x in c) else 0) + (8 if any(norm(x[0]) in extra for x in c) else 0)
        keep = sorted(sorted(chunks, key=score, reverse=True)[:3], key=lambda c: c[0][1]); chunks = keep
    if not chunks:
        cand = [w for w in ws if norm(w["w"]) not in WEAK and len(norm(w["w"])) >= 5]
        long = max(cand, key=lambda w: len(w["w"])) if cand else None
        if long: chunks = [[(long["w"].strip(",.;:!?\""), long["s"])]]
    return chunks

import difflib
WEAK = {"because", "created", "changed", "making", "moment", "afternoon", "officially", "other's", "succeed", "numbers", "personally", "nobody", "strange", "began"}
def align(words, text):
    """replace Whisper's spellings with the script's own words, keeping Whisper's timing"""
    script = [w for w in re.split(r"\s+", text.replace("—", " ").replace("–", " ")) if w]
    a = [norm(w["w"]) for w in words]; b = [norm(w) for w in script]
    out = [dict(w) for w in words]
    for op, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
        if op == "equal" or (op == "replace"):
            n1, n2 = i2 - i1, j2 - j1
            if op == "equal" or n1 == n2:
                for k in range(n1): out[i1 + k]["w"] = script[j1 + k]
            elif n1 > 0 and n2 > 0:  # merge/split: give the script words the span's timing
                s, e = words[i1]["s"], words[i2 - 1]["e"]; new = []
                for k in range(n2): new.append(dict(w=script[j1 + k], s=s + (e - s) * k / n2, e=s + (e - s) * (k + 1) / n2))
                out[i1:i2] = [None] * n1; out[i1] = new
    flat = []
    for x in out:
        if x is None: continue
        flat += x if isinstance(x, list) else [x]
    return flat

def build_shots():
    T = json.load(open(f"{FULL}/timeline.json")); shots = []
    for it in T["items"]:
        if it["kind"] == "chapter":
            sh = Shot(); sh.kind, sh.beat, sh.start, sh.end = "chapter", -1, it["start"], it["start"] + it["dur"]
            sh.title = it["title"]; sh.words, sh.kws, sh.p = [], [], {}; shots.append(sh); continue
        i = it["i"]; specs = SPEC.get(i, [("mascot", {})])
        if it["words"]: it["words"] = align(it["words"], BEATS[i]["text"])
        sents = sentences(it["words"]) if it["words"] else [[]]
        bounds = []
        for k, s in enumerate(sents):
            st = it["start"] if k == 0 else s[0]["s"] - 0.15
            en = (sents[k + 1][0]["s"] - 0.15) if k + 1 < len(sents) else it["start"] + it["dur"] + (0.45 if it["audio"] else 0.3)
            bounds.append((st, en, s))
        for k, (st, en, s) in enumerate(bounds):
            sh = Shot(); sh.kind, sh.p = specs[k % len(specs)]; sh.beat = i; sh.start, sh.end = st, en; sh.words = s
            sh.kws = keywords(s, sh.p.get("kw", [])) if s else []
            shots.append(sh)
    for k, sh in enumerate(shots): sh.idx = k; sh.solemn = sh.beat in SOLEMN or sh.p.get("solemn", False)
    return shots, T["total"]

# ======================= runtime state =======================
STATE = dict(now=0.0, rms=None, sr=100, years=[])
def mouth():
    r = STATE["rms"]; k = int(STATE["now"] * STATE["sr"])
    v = float(r[k]) if r is not None and 0 <= k < len(r) else 0
    return v * (0.55 + 0.45 * abs(math.sin(STATE["now"] * 21)))
def blink(): return (STATE["now"] % 3.3) < 0.11
def bob(): return math.sin(STATE["now"] * 3.2)
def M(img, x, y, s=1.0, **k): mascot2(img, x, y, s, mouth=mouth(), blink=blink(), bob=bob(), **k)
def walk_in(t, x0, x1, dur=1.0):
    k = clamp(t / dur); x = lerp(x0, x1, ease(k)); return x, (abs(x - x0) / 90.0) if k < 1 else None
def char(img, key, x, y, s=.8, **k):
    base = dict(CHARS[key]); base.update(k); person2(img, x, y, s, **base)

def kws_draw(img, sh, cx, cy, size=96, fill=INK, stroke=0, maxw=1050, spacing=1.25, sfill=(30, 30, 30)):
    styles_used = set(); n = len(sh.kws)
    for j, ch in enumerate(sh.kws):
        txt = " ".join(w for w, _ in ch); sz = size
        while sz > 40 and F(sz).getlength(txt) > maxw: sz -= 6
        hl = {}
        isnum = any(re.match(r"^\d", w) or norm(w) in NUMW for w, _ in ch)
        if isnum and "num" not in styles_used:
            for w, _ in ch:
                if re.match(r"^\d", w) or norm(w) in NUMW: hl[w] = "circle" if len(w) <= 5 else "red"
            styles_used.add("num")
        elif "marker" not in styles_used and not sh.solemn:
            hl[ch[-1][0]] = "marker"; styles_used.add("marker")
        elif "underline" not in styles_used and not sh.solemn:
            hl[ch[-1][0]] = "underline"; styles_used.add("underline")
        y = cy + (j - (n - 1) / 2) * sz * spacing
        if sh.solemn: hl = {}
        kin(img, (cx, y), ch, STATE["now"], sz, fill=fill, hl=hl, stroke=stroke, stroke_fill=sfill)

def first_kw_time(sh, default):
    return sh.kws[0][0][1] if sh.kws else default
def word_time(sh, word, default):
    for w in sh.words:
        if norm(w["w"]) == norm(word): return w["s"]
    return default
def pointing(sh):
    now = STATE["now"]; ts = [c[0][1] for c in sh.kws]
    return max([0.0] + [1 - clamp((now - t0) / 1.2) for t0 in ts if now >= t0]) * .6 + .25

# ======================= templates =======================
def T_mascot(img, sh, t):
    if sh.p.get("bg") == "room": img.paste(room_bg())
    M(img, 330, 1010, 1.05, point=pointing(sh), wave_arm=.15 + .2 * math.sin(t * 2), tilt=math.sin(t * .8) * .5, mood=sh.p.get("mood", "happy"))
    kws_draw(img, sh, 1150, 470, 110)

ICON_EXTRA = {}
def draw_icon(img, kind, x, y, s, t):
    if kind in ("police", "camp", "factory", "army", "money", "bread"): icon(img, kind, x, y, s, t); return
    if t <= 0: return
    d = ImageDraw.Draw(img); s *= back(t * 3); lw = max(2, int(5 * s))
    if kind == "scroll":
        d.rounded_rectangle([x - 80 * s, y - 60 * s, x + 80 * s, y + 60 * s], int(14 * s), fill=(240, 226, 190), outline=INK, width=lw)
        for k in range(3): d.line([x - 50 * s, y - 25 * s + k * 25 * s, x + 50 * s, y - 25 * s + k * 25 * s], fill=INK, width=max(1, lw - 2))
    elif kind == "eye":
        d.ellipse([x - 90 * s, y - 50 * s, x + 90 * s, y + 50 * s], fill=WHITE, outline=INK, width=lw)
        d.ellipse([x - 34 * s, y - 34 * s, x + 34 * s, y + 34 * s], fill=(80, 120, 170), outline=INK, width=lw); d.ellipse([x - 14 * s, y - 14 * s, x + 14 * s, y + 14 * s], fill=INK)
    elif kind == "files":
        for k in range(3): d.rectangle([x - 70 * s + k * 12 * s, y - 60 * s - k * 12 * s, x + 70 * s + k * 12 * s, y + 60 * s - k * 12 * s], fill=(250, 240, 210), outline=INK, width=lw)
    elif kind == "ring":
        d.ellipse([x - 60 * s, y - 60 * s, x + 60 * s, y + 60 * s], outline=(200, 170, 80), width=int(22 * s)); d.ellipse([x - 60 * s, y - 60 * s, x + 60 * s, y + 60 * s], outline=INK, width=lw)
    elif kind == "castle":
        d.rectangle([x - 70 * s, y - 40 * s, x + 70 * s, y + 60 * s], fill=(196, 186, 170), outline=INK, width=lw)
        for k in (-1, 1): d.rectangle([x + k * 70 * s - 22 * s, y - 90 * s, x + k * 70 * s + 22 * s, y + 60 * s], fill=(186, 176, 160), outline=INK, width=lw)

def T_icons(img, sh, t):
    ic = sh.p["icons"]; M(img, 250, 1010, .95, point=pointing(sh), tilt=.3)
    n = len(ic); x0 = 1150 - (n - 1) * 170
    for j, (kind, lab, trig) in enumerate(ic):
        ta = word_time(sh, trig, sh.start + .5 + j * .6)
        x = x0 + j * 340; draw_icon(img, kind, x, 520 + math.sin(STATE["now"] * 2 + j) * 6, 1.1, STATE["now"] - ta)
        kin(img, (x, 680), [(lab, ta + .1)], STATE["now"], 54)
    hdr = [c for c in sh.kws if not any(norm(w) in {norm(i[1]) for i in ic} or norm(w) in {norm(i[2]) for i in ic} for w, _ in c)][:1]
    if hdr:
        s2 = Shot(); s2.kws, s2.solemn = hdr, sh.solemn; kws_draw(img, s2, 1150, 200, 90)

def T_map(img, sh, t):
    p = sh.p; base = p.get("base", "eu"); key = f"{sh.beat}-{p.get('fills')}-{p.get('year')}-{base}"
    im, b = map_img(key, p.get("fills", []), p.get("year", 1938), base)
    lo, la, z0, z1 = p["view"]; k = ease(t / max(1, sh.end - sh.start))
    cx, cy = proj(im, b, lo, la); fr, box = cam(im, cx, cy, lerp(im.width * z0, im.width * z1, k)); img.paste(fr)
    if p.get("route"):
        pts = [to_screen(box, *proj(im, b, *q)) for q in p["route"]]; d = ImageDraw.Draw(img); segs = len(pts) - 1
        prog = clamp(t / 4.0) * segs
        for j in range(segs):
            f = clamp(prog - j)
            if f > 0:
                a, c = pts[j], pts[j + 1]; e = (lerp(a[0], c[0], f), lerp(a[1], c[1], f))
                mid = ((a[0] + e[0]) / 2, min(a[1], e[1]) - 80 * f)
                d.line([a, mid, e], fill=(255, 220, 80), width=7, joint="curve")
    for pi, pn in enumerate(p.get("pins", [])):
        plo, pla, lab, trig = pn; ta = word_time(sh, trig, sh.start + .6 + pi * .8)
        sx, sy = to_screen(box, *proj(im, b, plo, pla)); pin(img, sx, sy, STATE["now"] - ta)
        ly = sy + 70 if sy + 110 < H else sy - 120
        kin(img, (sx, ly), [(lab, ta + .2)], STATE["now"], 64, fill=WHITE, stroke=4)
    s2 = Shot(); s2.kws = [c for c in sh.kws if not any(norm(w) in {norm(x[2]) for x in p.get("pins", [])} for w, _ in c)]; s2.solemn = sh.solemn
    kws_draw(img, s2, W / 2, 170 + 60 * (len(s2.kws) - 1), 84, fill=WHITE, stroke=4)
    if p.get("base", "eu") != "world": M(img, 1720, 1180, .75, look=-1, mood="serious" if sh.beat in (33, 43, 56) else "happy")

def T_date(img, sh, t):
    M(img, 330, 1010, 1.0, point=pointing(sh), tilt=.3)
    calendar(img, 1250, 560, sh.p["date"], t * 1.5)
    s2 = Shot(); s2.kws = [c for c in sh.kws if not any(re.match(r"^\d", w) for w, _ in c)][:2]; s2.solemn = False
    kws_draw(img, s2, 1250, 170, 84)

def T_photo(img, sh, t):
    M(img, 260, 1010, .95, point=pointing(sh), tilt=.2)
    framed(img, PHOTOS[sh.p["photo"]], (640, 160, 1100, 760), t * 1.4)
    kws_draw(img, sh, 1500, 460, 84, maxw=700)

def T_rally(img, sh, t):
    now = STATE["now"]
    if sh.p.get("indoor"): img.paste(room_bg(wall=(214, 190, 150)))
    else: img.paste(sky_bg(t=t))
    podium(img, 960, 860); talking = True
    char(img, sh.p.get("speaker", "hitler"), 960, 610, .85, face=1 if int(now * 1.3) % 2 else -1, arm_r=.55 + .45 * abs(math.sin(now * 4)),
         mouth=abs(math.sin(now * 11)), mood="angry")
    n = sh.p.get("guards", 8); xs = [440, 560, 680, 800, 1120, 1240, 1360, 1480]
    sel = xs[4 - n // 2:4 + n // 2] if n < 8 else xs
    for j, x1 in enumerate(sel):
        x0 = -150 if x1 < 960 else W + 150; x, ph = walk_in(t - j * .08, x0, x1, 1.0); char(img, "ss", x, 930, .66, face=1 if x1 < 960 else -1, walk=ph)
    crowd(img)
    kws_draw(img, sh, 430, 260, 80, maxw=640)

def T_street(img, sh, t):
    mode = sh.p.get("mode", "crowd"); now = STATE["now"]
    if mode in ("night", "broken"):
        img.paste(sky_bg(sky_top=(20, 24, 50), sky_bot=(50, 50, 90), hills=False, clouds=False, horizon=760)); buildings(img, dark=True, broken=(mode == "broken"))
    else:
        img.paste(sky_bg(horizon=760, hills=False)); buildings(img, seed=sh.beat)
    if mode == "fight":
        lunge = math.sin(now * 5) * 30
        for j in range(3):
            person2(img, 470 + j * 140 + lunge, 1000, .72, coat=(150, 60, 50), face=1, arm_r=abs(math.sin(now * 7 + j)), mood="angry", walk=now * 1.5 + j * .3)
            char(img, "sa", 1450 - j * 140 - lunge, 1000, .72, face=-1, arm_r=abs(math.sin(now * 7 + j + 1)), mood="angry", walk=now * 1.5 + j * .3 + .5)
        d = ImageDraw.Draw(img, "RGBA")
        for k in range(6):
            r = 60 + 20 * math.sin(now * 6 + k); d.ellipse([820 + k * 50 - r, 800 - r + (k % 2) * 30, 820 + k * 50 + r, 800 + r + (k % 2) * 30], fill=(200, 190, 170, 170))
    elif mode == "crowd":
        for j in range(7):
            person2(img, 300 + j * 220, 1010, .7, coat=[(120, 60, 50), (90, 100, 130), (150, 110, 60), (80, 80, 90)][j % 4], face=1 if j < 3 else -1,
                    arm_r=.9 * abs(math.sin(now * 3 + j)) if j % 2 else 0, hat="flat" if j % 3 == 0 else None, mouth=.6 if j % 2 else 0)
        d = ImageDraw.Draw(img)
        for j, col in enumerate([(200, 40, 40), (40, 80, 160), (220, 180, 40)]):
            x = 520 + j * 440; d.line([x, 600, x, 900], fill=INK, width=6); d.rectangle([x, 600, x + 120, 680], fill=col, outline=INK, width=4)
    elif mode == "police":
        for j in range(4): char(img, "police", 1150 + j * 150, 1000, .72, face=-1, arm_r=.6)
        x0 = 300 + 60 * math.sin(now * 2)
        for j in range(4): char(img, "ss" if j % 2 else "sa", x0 + j * 150, 1000, .72, face=1, walk=now * 1.5 + j * .2)
    elif mode == "night":
        for j in range(3): char(img, "ss", 1200 + j * 150, 1000, .72, face=-1, arm_r=.7)
        for j in range(2): char(img, "sa", 600 + j * 150, 1000, .72, face=1, mood="surprised", arm_r=.9, arm_l=.9)
        car(img, 300, 1030, (40, 40, 44))
    kws_draw(img, sh, 960, 170, 96, fill=WHITE if mode in ("night", "broken") else INK, stroke=4 if mode in ("night", "broken") else 0)

def T_march(img, sh, t):
    img.paste(sky_bg(t=t)); who = sh.p.get("who", "ss"); now = STATE["now"]
    off = (now * 140) % 170
    for row, (y, s) in enumerate(((880, .6), (1010, .72))):
        for j in range(14):
            x = -200 + j * 170 + off + row * 60
            char(img, who, x, y, s, face=1, walk=now * 1.6 + j * .05, arm_r=0, collar=CHARS[who].get("collar", (230, 230, 230)))
    kws_draw(img, sh, 960, 200, 100)

def T_room(img, sh, t):
    img.paste(room_bg()); ppl = sh.p.get("people", []); now = STATE["now"]
    if sh.p.get("desk"):
        table(img, 300, 900, 760); char(img, ppl[0], 600, 900, .8, face=1, mood="neutral")
        d = ImageDraw.Draw(img); d.rectangle([380, 700, 500, 760], fill=(250, 240, 210), outline=INK, width=3)
        if len(ppl) > 1:
            x, ph = walk_in(t, W + 200, 1200, 1.4); char(img, ppl[1], x, 1000, .85, face=-1, walk=ph, mouth=abs(math.sin(now * 9)) if ph is None and int(now) % 3 == 0 else 0)
    else:
        n = len(ppl)
        for j, key in enumerate(ppl):
            x = 960 + (j - (n - 1) / 2) * 420
            talking = (int(now / 1.6) % n) == j
            char(img, key, x, 1000, .9, face=-1 if x > 960 else 1, arm_r=.6 * abs(math.sin(now * 3)) if talking else 0, mouth=abs(math.sin(now * 10)) * .8 if talking else 0, bob=math.sin(now * 2 + j) * .4)
    kws_draw(img, sh, 960 + (380 if sh.p.get("desk") else 0), 200, 90, maxw=900)

def T_eight(img, sh, t):
    M(img, 250, 1010, .95, mood="serious", tilt=.3)
    for j in range(8):
        x, ph = walk_in(t - j * .1, W + 120 + j * 60, 680 + j * 150, 1.1); char(img, "ss", x, 930, .72, face=-1, walk=ph, bob=0 if ph else math.sin(STATE["now"] * 3 + j) * .3)
        if ph is None: tag(img, (680 + j * 150, 480), str(j + 1), 1)
    kws_draw(img, sh, 1220, 220, 100)

def T_counter(img, sh, t):
    p = sh.p; v = p["value"] * ease(t / 1.6)
    M(img, 250, 1010, .95, point=.5, mood="surprised" if t > 1.6 else "happy")
    d = ImageDraw.Draw(img); s = back(t * 2)
    if s > 0: d.text((1150, 470), p.get("prefix", "") + f"{int(v):,}", font=F(int(170 * min(1.1, s))), fill=RED if t > 1.6 else INK, anchor="mm")
    kin(img, (1150, 640), [(p["label"], sh.start + .4)], STATE["now"], 64)
    if p["value"] >= 1000:  # tiny growing crowd of icons
        n = int(30 * ease(t / 1.6))
        for j in range(n): person2(img, 720 + (j % 15) * 62, 900 + (j // 15) * 90, .2, shadow=False, **SSMAN)

def T_title(img, sh, t):
    img.paste(sky_bg(ground=(40, 34, 44), horizon=820, sky_top=(46, 40, 78), sky_bot=(236, 140, 84), hills=False, clouds=False)); d = ImageDraw.Draw(img)
    for j in range(14):
        x = j * 150; h = 90 + (j * 71) % 150; d.rectangle([x, 820 - h, x + 130, 820], fill=(30, 26, 36))
        if j % 4 == 1: d.polygon([(x + 40, 820 - h), (x + 65, 820 - h - 80), (x + 90, 820 - h)], fill=(30, 26, 36))
    d.ellipse([1500, 640, 1660, 800], fill=(250, 200, 120)); T0 = sh.start
    kin(img, (960, 230), [(w, T0 + .15 * j) for j, w in enumerate(["THE", "ENTIRE", "HISTORY", "OF"])], STATE["now"], 72, fill=(250, 240, 220), sc=True)
    kin(img, (960, 370), [("THE", T0 + .9), ("SS", T0 + 1.1)], STATE["now"], 180, fill=(250, 240, 220), sc=True, hl={"SS": "red"})
    s2 = Shot(); s2.kws = sh.kws[-2:]; s2.solemn = False; kws_draw(img, s2, 960, 560, 52, fill=(250, 240, 220))
    x, ph = walk_in(t, -200, 960, 2.0); M(img, x, 1060, .6)

def T_lostwar(img, sh, t):
    M(img, 260, 1010, .95, mood="serious"); x, ph = walk_in(t, W + 150, 1300, 2.2)
    char(img, "soldier", x, 960, .85, face=-1, walk=ph, mood="sad", tilt=.6); kws_draw(img, sh, 1080, 240, 100)
    kin(img, (1080, 380), [("1914 - 1918", sh.start + 1.0)], STATE["now"], 64, fill=RED)

def T_shop(img, sh, t):
    img.paste(room_bg(wall=(222, 214, 196))); d = ImageDraw.Draw(img); shocked = t > 3.0
    person2(img, 1450, 790, .75, coat=(240, 240, 240), hair=(60, 40, 30), face=-1, mood="surprised" if shocked else "neutral", arm_r=.7 if shocked else 0, collar=(250, 250, 250))
    d.rectangle([1100, 640, 1800, 820], fill=(150, 100, 60), outline=INK, width=5); icon(img, "bread", 1230, 600, .8, 1)
    x, ph = walk_in(t, -200, 620, 1.6); char(img, "worker", x, 1000, .8, face=1, walk=ph, arm_r=.35, mood="sad" if t > 4 else "neutral"); basket(img, x + 200, 960)
    d.rounded_rectangle([700, 120, 1700, 330], 18, fill=(40, 40, 44)); d.text((1200, 170), "1 US dollar =", font=F(56), fill=(240, 240, 240), anchor="mm")
    v = 4.2 * 10 ** (12 * ease(t / 5)); d.text((1200, 265), f"{int(v):,} marks", font=F(72 if v < 1e9 else 62), fill=(250, 200, 80), anchor="mm")
    bubble(img, (560, 420), "My wages!", t - 4.0)

def basket(img, x, y, s=1.0, notes=1.0):
    d = ImageDraw.Draw(img)
    for k in range(int(9 * notes)):
        nx = x - 70 * s + (k % 5) * 34 * s; ny = y - 70 * s - (k // 5) * 26 * s; d.rectangle([nx, ny, nx + 60 * s, ny + 34 * s], fill=(150, 190, 140), outline=INK, width=2)
    d.polygon([(x - 100 * s, y - 50 * s), (x + 100 * s, y - 50 * s), (x + 76 * s, y + 40 * s), (x - 76 * s, y + 40 * s)], fill=(190, 140, 80), outline=INK)
    d.arc([x - 80 * s, y - 150 * s, x + 80 * s, y + 10 * s], 200, 340, fill=INK, width=int(6 * s))

def T_prison(img, sh, t):
    img.paste(room_bg(wall=(170, 176, 190), floor=(110, 110, 120))); bars(img, (760, 140, 1160, 460))
    if sh.p.get("writing"):
        table(img, 1100, 1700, 780); char(img, "hitler", 1400, 900, .8, face=-1, arm_r=.35 + .1 * math.sin(STATE["now"] * 8))
        d = ImageDraw.Draw(img); d.rectangle([1180, 720, 1320, 780], fill=(250, 240, 210), outline=INK, width=3)
    else:
        char(img, "hitler", 1300, 1000, .85, face=-1, mood="sad", tilt=.5)
    kws_draw(img, sh, 480, 300, 90, maxw=700)

def T_farm(img, sh, t):
    img.paste(sky_bg(t=t)); barn(img, 600, 800); chickens(img, STATE["now"])
    char(img, "official", 1000, 980, .8, face=1, glasses=True, mustache=True, mood="sad" if sh.p.get("kw") == ["poultry", "farm"] else "neutral", arm_r=.3)
    kws_draw(img, sh, 1250, 230, 96, maxw=1000)

def T_files(img, sh, t):
    img.paste(room_bg(wall=(214, 206, 190))); cabinet(img, 380, 900)
    labels = [" ".join(w for w, _ in c) for c in sh.kws] or ["FILE"]
    for j, ch in enumerate(sh.kws or [[("files", sh.start)]]):
        lab = " ".join(w for w, _ in ch)[:16]
        card(img, 1000 + j * 330, 420 + (j % 2) * 260, lab, STATE["now"] - ch[0][1], rot=(j * 7 % 11) - 5)
    char(img, "ss", 1650, 1000, .8, face=-1, arm_r=.5, glasses=False)

def T_duo(img, sh, t):
    img.paste(room_bg(wall=(206, 200, 196)))
    x1, ph1 = walk_in(t, -200, 640, 1.2); x2, ph2 = walk_in(t - .3, W + 200, 1280, 1.2)
    char(img, "himmler", x1, 1000, .95, face=1, walk=ph1, arm_r=.4 if ph1 is None else 0)
    char(img, "heydrich", x2, 1000, 1.0, face=-1, walk=ph2, mood="neutral")
    tag(img, (640, 520), "Himmler", clamp(t - 1.2)); tag(img, (1280, 480), "Heydrich", clamp(t - 1.5))
    if sh.p.get("caption"): kin(img, (960, 200), [("Vision", sh.start + .5), ("+", sh.start + .8), ("Machine", sh.start + 1.1)], STATE["now"], 110, hl={"Machine": "marker"})
    else: kws_draw(img, sh, 960, 180, 90)

def T_fire(img, sh, t):
    img.paste(sky_bg(sky_top=(30, 30, 60), sky_bot=(120, 60, 50), hills=False, clouds=False)); d = ImageDraw.Draw(img)
    d.rectangle([460, 420, 1460, 820], fill=(170, 160, 140), outline=INK, width=6); d.ellipse([810, 250, 1110, 500], fill=(120, 140, 130), outline=INK, width=6)
    for k in range(8): d.rectangle([520 + k * 115, 520, 570 + k * 115, 640], fill=(240, 150, 60) if k % 2 else (60, 50, 50), outline=INK, width=3)
    for k in range(4): fire(img, 620 + k * 230, 470, STATE["now"] + k, 1.1)
    kws_draw(img, sh, 960, 140, 96, fill=WHITE, stroke=4)

def T_camp(img, sh, t):
    img.paste(sky_bg(sky_top=(150, 156, 166), sky_bot=(200, 200, 204), ground=(120, 120, 110), hills=False, clouds=False)); d = ImageDraw.Draw(img)
    for k in range(-1, 26): d.line([k * 80, 560, k * 80, 860], fill=INK, width=6)
    for yy in (600, 680, 760, 840): d.line([0, yy, W, yy], fill=(100, 100, 100), width=3)
    d.rectangle([1500, 260, 1640, 400], fill=(110, 90, 70), outline=INK, width=5); d.polygon([(1480, 260), (1570, 200), (1660, 260)], fill=(80, 60, 50), outline=INK)
    d.line([1520, 400, 1500, 860], fill=INK, width=8); d.line([1620, 400, 1640, 860], fill=INK, width=8)
    kws_draw(img, sh, 760, 250, 90, maxw=1100)

def T_org(img, sh, t):
    p = sh.p; d = ImageDraw.Draw(img); now = STATE["now"]
    if p.get("stack"):
        items = ["SD", "Dachau", "Gestapo", "Police", "RSHA", "Waffen-SS", "WVHA"]
        for j, lab in enumerate(items):
            ta = sh.start + .3 + j * (max(1.0, sh.end - sh.start - 1.0) / len(items)); a = back((now - ta) * 3)
            if a > 0:
                y = 960 - j * 120; w = 520 * a; d.rounded_rectangle([1150 - w / 2, y - 48, 1150 + w / 2, y + 48], 14, fill=[(196, 40, 40), (60, 60, 64)][j % 2], outline=INK, width=4)
                if a > .8: d.text((1150, y), lab, font=F(60), fill=WHITE, anchor="mm")
        M(img, 330, 1010, 1.0, point=.7); kin(img, (1150, 110), [("1929", sh.start + .2), ("→", sh.start + .4), ("1945", sh.end - 1.0)], now, 80, hl={"1945": "red"}); return
    boxes = p["boxes"]; pos = []
    for j, (lab, trig, x, y) in enumerate(boxes):
        ta = word_time(sh, trig, sh.start + .3 + j * .5) if trig else sh.start + .3 + j * .5; pos.append((x, y, ta))
    for a_, b_ in p.get("links", []):
        xa, ya, ta = pos[a_]; xb, yb, tb = pos[b_]; k = ease((now - max(ta, tb)) / .5)
        if k > 0: d.line([xa, ya + 60, lerp(xa, xb, k), lerp(ya + 60, yb - 60, k)], fill=INK, width=7)
    for j, (lab, trig, x, y) in enumerate(boxes):
        a = back((now - pos[j][2]) * 3)
        if a <= 0: continue
        small = p.get("tiny") == j; w = (360 if not small else 160) * a; h = (120 if not small else 70) * a
        col = (196, 40, 40) if lab.startswith(("SS", "WAFFEN", "RSHA", "ORDER")) else (60, 60, 64) if lab in ("HITLER", "NSDAP", "DACHAU", "GESTAPO", "KRIPO", "SD") else (150, 110, 60)
        d.rounded_rectangle([x - w / 2, y - h / 2, x + w / 2, y + h / 2], 16, fill=col, outline=INK, width=5)
        if a > .8: d.text((x, y), lab, font=F(64 if not small else 40), fill=WHITE, anchor="mm")
        if p.get("cross") == j and now - pos[j][2] > .8:
            k = ease((now - pos[j][2] - .8) / .4); d.line([x - w / 2, y + h / 2, lerp(x - w / 2, x + w / 2, k), lerp(y + h / 2, y - h / 2, k)], fill=RED, width=12)
    kws_draw(img, Shot.__new__(Shot) if False else type("S", (), dict(kws=[c for c in sh.kws if not any(norm(w) in {norm(b[0]) for b in boxes} for w, _ in c)][:1], solemn=sh.solemn))(), 960, 110, 80)

def T_flow(img, sh, t):
    d = ImageDraw.Draw(img); now = STATE["now"]; steps = [("GESTAPO ARREST", (60, 60, 64)), ("NO TRIAL", (150, 110, 60)), ("SS CAMP", (196, 40, 40))]
    for j, (lab, col) in enumerate(steps):
        ta = sh.start + .4 + j * .9; a = back((now - ta) * 3)
        if a <= 0: continue
        x = 420 + j * 540; w, h = 420 * a, 150 * a
        d.rounded_rectangle([x - w / 2, 540 - h / 2, x + w / 2, 540 + h / 2], 18, fill=col, outline=INK, width=5)
        if a > .8: d.text((x, 540), lab, font=F(56), fill=WHITE, anchor="mm")
        if j and a > .8: d.polygon([(x - 300, 520), (x - 250, 540), (x - 300, 560)], fill=INK); d.line([x - 330, 540, x - 260, 540], fill=INK, width=8)
    kws_draw(img, sh, 960, 220, 84)

def T_castle(img, sh, t):
    img.paste(sky_bg(t=t, sky_top=(150, 170, 200), sky_bot=(210, 220, 230))); castle(img)
    d = ImageDraw.Draw(img, "RGBA"); d.rectangle([0, 0, W, H], fill=(230, 230, 240, int(60 + 30 * math.sin(STATE["now"]))))
    kws_draw(img, sh, 960, 160, 96)

def T_expedition(img, sh, t):
    img.paste(sky_bg(t=t, ground=(220, 220, 230), hills=False)); d = ImageDraw.Draw(img)
    for x, h in ((300, 420), (800, 560), (1350, 480), (1750, 380)):
        d.polygon([(x - 360, 760), (x, 760 - h), (x + 360, 760)], fill=(140, 140, 160), outline=INK); d.polygon([(x - 90, 760 - h + 110), (x, 760 - h), (x + 90, 760 - h + 110)], fill=WHITE)
    for j in range(3): char(img, "official", 700 + j * 200 + (STATE["now"] * 40) % 60, 1000, .65, face=1, walk=STATE["now"] * 1.5 + j * .3, hat="flat")
    kin(img, (1300, 900), [("PSEUDOSCIENCE", sh.start + 1.2)], STATE["now"], 110, fill=RED, stroke=6, stroke_fill=WHITE, sc=True)
    kws_draw(img, sh, 960, 160, 90)

def T_hq(img, sh, t):
    img.paste(sky_bg(t=t, hills=False)); d = ImageDraw.Draw(img)
    d.rectangle([360, 300, 1560, 780], fill=(200, 190, 170), outline=INK, width=6); d.rectangle([330, 260, 1590, 310], fill=(170, 160, 140), outline=INK, width=5)
    for r in range(3):
        for c in range(8): d.rectangle([420 + c * 140, 340 + r * 130, 480 + c * 140, 430 + r * 130], fill=(70, 90, 120), outline=INK, width=3)
    d.rectangle([880, 640, 1040, 780], fill=(90, 60, 40), outline=INK, width=5)
    char(img, "ss", 800, 1000, .7, face=1); char(img, "ss", 1120, 1000, .7, face=-1)
    kin(img, (960, 200), [("GE", sh.start + .5), ("STA", sh.start + .8), ("PO", sh.start + 1.1)], STATE["now"], 110, fill=WHITE, stroke=6, hl={"PO": "red"})
    s2 = type("S", (), dict(kws=[c for c in sh.kws if norm(c[0][0]) not in ("gestapo",)][:2], solemn=False))(); kws_draw(img, s2, 960, 900, 70, fill=WHITE, stroke=4)

def T_solemn(img, sh, t):
    p = sh.p
    if p.get("map"):
        lo, la, z = p["map"]; im, b = map_img(f"dark-{sh.beat}", [], 1938, "eu", dark=.55); cx, cy = proj(im, b, lo, la)
        fr, box = cam(im, cx, cy, im.width * lerp(z, z * .9, ease(t / 8))); img.paste(fr); d = ImageDraw.Draw(img, "RGBA")
        for j, (mlo, mla) in enumerate(p.get("marks", [])):
            a = ease((t - .8 - j * .6) * 2)
            if a > 0:
                sx, sy = to_screen(box, *proj(im, b, mlo, mla)); r = 16 * a
                d.ellipse([sx - r * 2.2, sy - r * 2.2, sx + r * 2.2, sy + r * 2.2], fill=(180, 20, 20, 60)); d.ellipse([sx - r, sy - r, sx + r, sy + r], fill=(200, 30, 30, 230))
                if p.get("labels"): kin(img, (sx, sy + 56), [(p["labels"][j], sh.start + .9 + j * .6)], STATE["now"], 50, fill=WHITE, stroke=3, wobble=0)
    else:
        img.paste(Image.new("RGB", (W, H), (16, 16, 18)))
    if p.get("text"):
        for j, line in enumerate(p["text"]): kin(img, (W / 2, H / 2 - 60 + j * 130), [(line, sh.start + .5 + j * 1.6)], STATE["now"], 110 if j == 0 else 70, fill=WHITE, wobble=0)
    else:
        kws_draw(img, sh, W / 2, 180 if p.get("map") else H / 2, 96 if not p.get("map") else 80, fill=(236, 232, 226), stroke=3 if p.get("map") else 0)

def T_ruins(img, sh, t):
    img.paste(sky_bg(sky_top=(110, 110, 120), sky_bot=(180, 170, 160), hills=False, clouds=False)); ruins(img)
    d = ImageDraw.Draw(img, "RGBA")
    for k in range(5):  # smoke
        y = 500 - ((STATE["now"] * 30 + k * 80) % 400); d.ellipse([300 + k * 300 - 60, y - 60, 300 + k * 300 + 60, y + 60], fill=(80, 80, 84, 90))
    if sh.p.get("text"):
        for j, line in enumerate(sh.p["text"]): kin(img, (W / 2, 220 + j * 110), [(line, sh.start + .5 + j * 1.0)], STATE["now"], 90 if j == 0 else 60, fill=WHITE, stroke=4, wobble=0)
    else: kws_draw(img, sh, 960, 200, 96, fill=WHITE, stroke=4)
    if not sh.p.get("solemn"): M(img, 1700, 1180, .75, look=-1, mood="serious")

def T_bunker(img, sh, t):
    img.paste(Image.new("RGB", (W, H), (34, 32, 36))); d = ImageDraw.Draw(img, "RGBA")
    d.rectangle([0, 760, W, H], fill=(50, 46, 48)); d.line([960, 0, 960, 220], fill=(20, 20, 20), width=6)
    d.polygon([(900, 220), (1020, 220), (980, 180), (940, 180)], fill=(60, 60, 60)); d.polygon([(860, 230), (1060, 230), (1400, 900), (520, 900)], fill=(255, 230, 160, 40))
    d.ellipse([930, 220, 990, 270], fill=(255, 230, 160))
    table(img, 700, 1220, 760); d.rectangle([800, 700, 1100, 760], fill=(240, 236, 220), outline=INK, width=3)
    kws_draw(img, sh, 960, 420, 90, fill=WHITE, stroke=4)

def T_escape(img, sh, t):
    img.paste(sky_bg(t=t, sky_top=(140, 150, 170), sky_bot=(200, 200, 205))); now = STATE["now"]
    caught = sh.p.get("caught")
    x, ph = (walk_in(t, -200, 820, 2.5) if not caught else (820, None))
    person2(img, x, 1000, .85, coat=(110, 110, 104), trousers=(80, 80, 76), hat="flat", face=1, walk=ph, mood="surprised" if caught else "neutral")
    d = ImageDraw.Draw(img); hx, hy = x + 18 * .85, 1000 - 358 * .85                     # eyepatch over one eye
    d.ellipse([hx - 24 * .85 - 18, hy - 14, hx - 24 * .85 + 18, hy + 22], fill=INK); d.line([hx - 70, hy - 30, hx + 60, hy - 10], fill=INK, width=4)
    if caught:
        for j in range(2): char(img, "brit", 1180 + j * 170, 1000, .85, face=-1, arm_r=.8)
        bubble(img, (1180, 420), "Papers, please.", t - .4)
    kws_draw(img, sh, 960, 180, 90)

def T_court(img, sh, t):
    img.paste(room_bg(wall=(200, 186, 160))); d = ImageDraw.Draw(img)
    d.rectangle([700, 520, 1220, 760], fill=(110, 76, 50), outline=INK, width=6)
    char(img, "judge", 960, 600, .8, face=0, mouth=abs(math.sin(STATE["now"] * 9)) * .6 if t > 1 else 0)
    for j in range(4): char(img, "ss", 260 + j * 150, 1010, .62, face=1, mood="sad", hat=None, hair=(70, 60, 50))
    for j in range(2): char(img, "soldier", 1550 + j * 170, 1010, .66, face=-1)
    kws_draw(img, sh, 960, 170, 90)

def T_end(img, sh, t):
    M(img, 330, 1010, 1.05, wave_arm=.6 + .3 * math.sin(t * 8), point=.3)
    d = ImageDraw.Draw(img); s = back(t * 2)
    if s > 0:
        w, h = 900 * s, 506 * s; d.rounded_rectangle([1200 - w / 2, 520 - h / 2, 1200 + w / 2, 520 + h / 2], 24, fill=(30, 30, 34), outline=INK, width=6)
        if s > .9: d.text((1200, 470), "The Entire History", font=F(70), fill=WHITE, anchor="mm"); d.text((1200, 570), "of HITLER", font=F(96), fill=RED, anchor="mm")
    kin(img, (1200, 900), [("Watch", sh.start + .6), ("next", sh.start + .8)], STATE["now"], 90, hl={"next": "marker"})

def T_chapter(img, sh, t):
    img.paste(Image.new("RGB", (W, H), (26, 26, 30))); title = sh.title
    m = re.match(r"(CHAPTER \d+): (.*)", title)
    if m: top, main = m.group(1).title(), m.group(2).title()
    else: top, main = "", title.title()
    main = main.replace("Ss", "SS").replace("Sa ", "SA ").replace("(1930S)", "(1930s)")
    kin(img, (W / 2, 420), [(top, sh.start + .2)], STATE["now"], 60, fill=(200, 196, 190), wobble=0)
    words = main.split(); kin(img, (W / 2, 560), [(w, sh.start + .4 + j * .12) for j, w in enumerate(words)], STATE["now"], 110 if len(main) < 26 else 84, fill=(250, 240, 220), sc=True)
    d = ImageDraw.Draw(img); k = ease((t - .6) / .8); d.rectangle([W / 2 - 300 * k, 680, W / 2 + 300 * k, 690], fill=RED)

TEMPLATES = dict(mascot=T_mascot, icons=T_icons, map=T_map, date=T_date, photo=T_photo, rally=T_rally, street=T_street, march=T_march,
                 room=T_room, eight=T_eight, counter=T_counter, title=T_title, lostwar=T_lostwar, shop=T_shop, prison=T_prison, farm=T_farm,
                 files=T_files, duo=T_duo, fire=T_fire, camp=T_camp, org=T_org, flow=T_flow, castle=T_castle, expedition=T_expedition,
                 hq=T_hq, solemn=T_solemn, ruins=T_ruins, bunker=T_bunker, escape=T_escape, court=T_court, end=T_end, chapter=T_chapter)

# ======================= frame render =======================
SHOTS, TOTAL = None, None
def setup():
    global SHOTS, TOTAL
    SHOTS, TOTAL = build_shots()
    # lip-sync envelope for the whole timeline (100 Hz)
    env = np.zeros(int(TOTAL * 100) + 10)
    for it in json.load(open(f"{FULL}/timeline.json"))["items"]:
        if it.get("audio"):
            w = wave.open(it["audio"]); sr = w.getframerate(); a = np.frombuffer(w.readframes(w.getnframes()), np.int16 if w.getsampwidth() == 2 else np.int32).astype(np.float32)
            a /= (np.abs(a).max() + 1e-9); hop = sr // 100; n = len(a) // hop
            r = np.sqrt((a[:n * hop].reshape(n, hop) ** 2).mean(1)); s0 = int(it["start"] * 100); env[s0:s0 + n] = r[:len(env) - s0]
    STATE["rms"] = np.clip(env / (np.percentile(env[env > 0], 95) + 1e-9), 0, 1); STATE["sr"] = 100
    # year badge track
    ys = []
    for it in json.load(open(f"{FULL}/timeline.json"))["items"]:
        for w in it.get("words", []):
            m = re.match(r"^(19[0-4]\d)", w["w"].strip(",."))
            if m: ys.append((w["s"], m.group(1)))
    STATE["years"] = ys

def shot_at(tt):
    for sh in SHOTS:
        if sh.start <= tt < sh.end: return sh
    return SHOTS[-1] if tt >= SHOTS[-1].start else SHOTS[0]

def raw_frame(tt):
    STATE["now"] = tt; sh = shot_at(tt); img = grey_bg()
    if sh.kind in TEMPLATES: TEMPLATES[sh.kind](img, sh, tt - sh.start)
    if sh.kind not in ("chapter", "title", "end") and not (sh.kind == "solemn" and not sh.p.get("map")):
        yr = [y for (ts, y) in STATE["years"] if ts <= tt]
        if yr: badge(img, yr[-1], 1)
    k = clamp((tt - sh.start) / max(.5, sh.end - sh.start)); z = 1.0 + (.02 if sh.solemn else .035) * k
    sh_x = min(10 * k, (W - W / z) / 2)
    if z > 1.0001: img = img.resize((W, H), Image.BILINEAR, box=((W - W / z) / 2 + sh_x, (H - H / z) / 2, (W + W / z) / 2 + sh_x, (H + H / z) / 2))
    return img, sh

TD = 0.32
def frame(tt):
    img, sh = raw_frame(tt)
    k = tt - sh.start
    if sh.idx > 0 and k < TD:
        prev = SHOTS[sh.idx - 1]; out_img, _ = raw_frame(sh.start - 1 / FPS); STATE["now"] = tt; e = ease(k / TD)
        if sh.solemn or prev.solemn or sh.kind == "chapter" or prev.kind == "chapter": return Image.blend(out_img, img, e)
        kind = ["slide", "circle", "zoom"][sh.idx % 3]
        if kind == "slide":
            fr = Image.new("RGB", (W, H)); fr.paste(out_img.filter(ImageFilter.BoxBlur(6)), (int(-W * e), 0)); fr.paste(img.filter(ImageFilter.BoxBlur(int(8 * (1 - e)))), (int(W * (1 - e)), 0)); return fr
        if kind == "circle":
            m = Image.new("L", (W, H), 0); r = 1200 * e; ImageDraw.Draw(m).ellipse([W / 2 - r, H / 2 - r, W / 2 + r, H / 2 + r], fill=255); return Image.composite(img, out_img, m)
        z = 1 + .5 * e; zo = out_img.resize((W, H), Image.BILINEAR, box=((W - W / z) / 2, (H - H / z) / 2, (W + W / z) / 2, (H + H / z) / 2)); return Image.blend(zo, img, e)
    return img

def render_segment(k, n):
    setup(); N = int(TOTAL * FPS); a, b = N * k // n, N * (k + 1) // n
    p = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                          "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", f"{FULL}/seg_{k}.mp4"], stdin=subprocess.PIPE)
    for fi in range(a, b):
        p.stdin.write(frame(fi / FPS).tobytes())
        if (fi - a) % 900 == 0: print(f"seg{k} {fi / FPS:.0f}s/{b / FPS:.0f}s", flush=True)
    p.stdin.close(); p.wait(); print(f"seg{k} done", flush=True)

# ======================= audio =======================
def load_wav(p, sr_out=44100):
    w = wave.open(p); sr = w.getframerate(); ch = w.getnchannels(); sw = w.getsampwidth()
    a = np.frombuffer(w.readframes(w.getnframes()), np.int16 if sw == 2 else np.int32).astype(np.float32) / (32768 if sw == 2 else 2 ** 31)
    if ch > 1: a = a.reshape(-1, ch).mean(1)
    if sr != sr_out: a = np.interp(np.arange(int(len(a) * sr_out / sr)) * sr / sr_out, np.arange(len(a)), a)
    return a

def build_audio():
    setup(); sys.path.insert(0, SAMPLE); import music as MU
    SR = 44100; n = int(TOTAL * SR) + SR; voice = np.zeros(n); fx = np.zeros(n)
    TL = json.load(open(f"{FULL}/timeline.json"))
    for it in TL["items"]:
        if it.get("audio"):
            a = load_wav(it["audio"]); s0 = int(it["start"] * SR); voice[s0:s0 + len(a)] += a[:n - s0]
    voice /= (np.abs(voice).max() + 1e-9); voice *= .9
    mus = MU.music(TOTAL + 1); mus = np.pad(mus, (0, max(0, n - len(mus))))[:n]
    t = np.arange(n) / SR
    drone = (np.sin(2 * np.pi * 55 * t) * .5 + np.sin(2 * np.pi * 82.4 * t) * .3) * (.7 + .3 * np.sin(2 * np.pi * .1 * t))
    sol = np.zeros(n)
    for sh in SHOTS:
        if sh.solemn: sol[int(sh.start * SR):int(sh.end * SR)] = 1
    def smooth(x, k):
        c = np.cumsum(np.concatenate([[0.0], x])); y = (c[k:] - c[:-k]) / k
        pad = (len(x) - len(y)); return np.concatenate([np.full(pad // 2, y[0]), y, np.full(pad - pad // 2, y[-1])])
    sol = smooth(sol, int(1.5 * SR))             # smooth fades between modes
    venv = smooth(np.abs(voice), 4410); duck = 1 - .55 * np.clip(venv / (venv.max() * .3 + 1e-9), 0, 1)
    bed = mus * .30 * duck * (1 - sol) + drone * .05 * sol
    sfx = {name: load_wav(f"{SAMPLE}/audio/sfx_{name}.wav") for name in ("pop", "whoosh", "ding")}
    def put(name, tt, g):
        a = sfx[name] * g; s0 = int(tt * SR); fx[s0:s0 + len(a)] += a[:max(0, n - s0)]
    for sh in SHOTS[1:]:
        if not sh.solemn and not SHOTS[sh.idx - 1].solemn: put("whoosh", sh.start - .05, .35)
        if sh.solemn: continue
        for c in sh.kws: put("pop", c[0][1], .22)
        if sh.kind == "counter": put("ding", sh.start + 1.6, .4)
    mix = voice + bed + fx
    rms = np.sqrt(np.mean(mix[mix != 0] ** 2)); mix *= (10 ** (-16 / 20) * 1.4) / (rms + 1e-9); mix = np.tanh(mix * 1.1) / 1.1
    out = (np.clip(mix, -1, 1) * 32767).astype(np.int16); out = np.stack([out, out], 1)
    w = wave.open(f"{FULL}/mix.wav", "wb"); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(out.tobytes()); w.close()
    # chapters for the description
    lines = []
    for sh in SHOTS:
        if sh.kind == "chapter":
            m = int(sh.start); lines.append(f"{m // 60:02d}:{m % 60:02d} " + re.sub(r"^CHAPTER \d+: ", "", sh.title).title().replace("Ss", "SS").replace("(1930S)", "(1930s)"))
    open(f"{FULL}/chapters.txt", "w").write("00:00 Intro\n" + "\n".join(lines)); print("audio ok", TOTAL)

if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "prep": prep()
    elif cmd == "still":
        setup()
        for a in sys.argv[2:]: frame(float(a)).save(f"{FULL}/chk_{a}.png")
    elif cmd == "seg": render_segment(int(sys.argv[2]), int(sys.argv[3]))
    elif cmd == "audio": build_audio()
    elif cmd == "patch":
        setup(); a, b = float(sys.argv[2]), float(sys.argv[3])
        p = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                              "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", f"{FULL}/patch.mp4"], stdin=subprocess.PIPE)
        for fi in range(int(a * FPS), int(b * FPS)): p.stdin.write(frame(fi / FPS).tobytes())
        p.stdin.close(); p.wait(); print("patch ok")
    elif cmd == "shots":
        setup()
        for sh in SHOTS: print(f"{sh.start:7.1f} {sh.end - sh.start:5.1f} b{sh.beat:<3} {sh.kind:<10} {[ ' '.join(w for w, _ in c) for c in sh.kws]}")
