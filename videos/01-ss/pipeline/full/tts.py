import json, sys, numpy as np, soundfile as sf, wave
from kokoro_onnx import Kokoro
S, F = sys.argv[1], sys.argv[2]
beats = json.load(open('/tmp/claude-0/-home-user-LifeHacker14/90ebba43-d755-5558-a675-5caff7c9482b/scratchpad/video/build/beats.json'))
k = Kokoro(f'{S}/kokoro/kokoro-v1.0.onnx', f'{S}/kokoro/voices-v1.0.bin')
for i, b in enumerate(beats):
    t = b['text'].replace('Reichsführer', 'Reichs-fuehrer').replace('–', ', ').replace('—', ', ')
    if not t.strip(): continue
    a, sr = k.create(t, voice='am_michael', speed=1.0, lang='en-us')
    sf.write(f'{F}/vo/{i:02d}.wav', a, sr); print(i, round(len(a)/sr, 1), flush=True)
