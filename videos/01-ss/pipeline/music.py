"""Synthesised, copyright-free explainer music bed + sound effects (numpy only)."""
import numpy as np, wave, sys

SR = 44100


def save(path, x):
    x = np.clip(x, -1, 1); x = (x * 32767).astype(np.int16)
    if x.ndim == 1: x = np.stack([x, x], 1)
    w = wave.open(path, "wb"); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(x.tobytes()); w.close()


def env(n, a=0.005, d=0.4):
    t = np.arange(n) / SR
    return np.minimum(1, t / a) * np.exp(-t / d)


def marimba(f, dur=0.6):
    n = int(dur * SR); t = np.arange(n) / SR
    return (np.sin(2 * np.pi * f * t) + 0.25 * np.sin(2 * np.pi * f * 4 * t) * np.exp(-t / 0.05)) * env(n, 0.002, 0.25)


def pluck(f, dur=0.5):  # Karplus-Strong
    n = int(dur * SR); p = int(SR / f); buf = np.random.uniform(-1, 1, p); out = np.zeros(n)
    for i in range(n):
        out[i] = buf[i % p]; buf[i % p] = 0.5 * (buf[i % p] + buf[(i + 1) % p]) * 0.996
    return out * 0.6


def bass(f, dur=0.45):
    n = int(dur * SR); t = np.arange(n) / SR
    return (np.sin(2 * np.pi * f * t) + 0.3 * np.sin(2 * np.pi * 2 * f * t)) * env(n, 0.005, 0.3)


def hat(dur=0.05):
    n = int(dur * SR); x = np.random.uniform(-1, 1, n); x = np.diff(np.concatenate([[0], x]))
    return x * env(n, 0.001, 0.015) * 0.3


def note(m): return 440 * 2 ** ((m - 69) / 12)


def music(total, bpm=104):
    beat = 60 / bpm; out = np.zeros(int((total + 2) * SR))
    def put(x, t, g=1.0):
        i = int(t * SR); out[i:i + len(x)] += g * x[:max(0, len(out) - i)]
    # C - Am - F - G, playful arpeggio
    chords = [(60, 64, 67), (57, 60, 64), (53, 57, 60), (55, 59, 62)]
    roots = [36, 33, 29, 31]
    pattern = [0, 1, 2, 1, 0, 2, 1, 2]
    t = 0.0; bar = 0
    pl_cache = {}
    while t < total:
        ch = chords[bar % 4]
        for k, idx in enumerate(pattern):
            m = ch[idx] + (12 if k in (2, 5) else 0)
            put(marimba(note(m)), t + k * beat / 2, 0.22)
            put(hat(), t + k * beat / 2, 0.35 if k % 2 else 0.15)
        put(bass(note(roots[bar % 4])), t, 0.5); put(bass(note(roots[bar % 4])), t + 2.5 * beat, 0.35)
        if bar % 2 == 1:
            key = ch[2] + 12
            if key not in pl_cache: pl_cache[key] = pluck(note(key), 0.6)
            put(pl_cache[key], t + 3 * beat, 0.25)
        t += 4 * beat; bar += 1
    out = out[:int(total * SR)]
    fade = int(3 * SR); out[-fade:] *= np.linspace(1, 0, fade); out[:int(1 * SR)] *= np.linspace(0, 1, int(1 * SR))
    return out / (np.abs(out).max() + 1e-9) * 0.5


def sfx_pop():
    n = int(0.12 * SR); t = np.arange(n) / SR; f = 900 * np.exp(-t / 0.03) + 300
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * env(n, 0.001, 0.04) * 0.6


def sfx_whoosh():
    n = int(0.4 * SR); x = np.random.uniform(-1, 1, n)
    # crude band-pass sweep via moving average of different lengths
    out = np.zeros(n)
    for i in range(0, n, 512):
        k = int(2 + 30 * (1 - i / n)); seg = np.convolve(x[i:i + 512 + k], np.ones(k) / k, "valid")[:512]
        out[i:i + len(seg)] = seg
    e = np.sin(np.linspace(0, np.pi, n)) ** 2
    return out * e * 1.2


def sfx_click():
    n = int(0.03 * SR); return np.random.uniform(-1, 1, n) * env(n, 0.0005, 0.006) * 0.25


def sfx_ding():
    n = int(0.6 * SR); t = np.arange(n) / SR
    return (np.sin(2 * np.pi * 1318 * t) + 0.5 * np.sin(2 * np.pi * 1976 * t)) * env(n, 0.002, 0.18) * 0.35


if __name__ == "__main__":
    out = sys.argv[1]; total = float(sys.argv[2])
    save(f"{out}/music.wav", music(total))
    for name, fn in [("pop", sfx_pop), ("whoosh", sfx_whoosh), ("click", sfx_click), ("ding", sfx_ding)]:
        save(f"{out}/sfx_{name}.wav", fn())
    print("ok")
