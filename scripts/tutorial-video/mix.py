"""Build soundtrack (arrival chimes + soft tap clicks) and encode the final mp4."""
import json, sys, subprocess, glob, wave
import numpy as np
outdir, dest, trim = sys.argv[1], sys.argv[2], float(sys.argv[3]) if len(sys.argv) > 3 else 1.0
meta = json.load(open(f'{outdir}/meta.json'))
SR = 44100
dur = meta['dur'] + 2
track = np.zeros(int(SR * dur))

def chime():
    n = int(SR * 0.95); t = np.arange(n) / SR; out = np.zeros(n)
    for f0, st in [(659.25, 0.0), (880.0, 0.18)]:
        tt = t - st; m = tt >= 0
        env = np.where(m, np.minimum(1, tt / 0.015) * np.exp(-np.clip(tt, 0, None) * 6.5), 0)
        out += env * (np.sin(2 * np.pi * f0 * tt) + 0.25 * np.sin(2 * np.pi * 2 * f0 * tt))
    return out * 0.35

def click():
    n = int(SR * 0.05); t = np.arange(n) / SR
    return np.sin(2 * np.pi * 1800 * t) * np.exp(-t * 120) * 0.12

def add(sig, at):
    i = int(at * SR)
    if i < 0 or i >= len(track): return
    j = min(len(track), i + len(sig)); track[i:j] += sig[:j - i]

for c in meta['chimes']: add(chime(), c)
for tp in meta['taps']: add(click(), tp)
track = np.clip(track, -1, 1)
with wave.open(f'{outdir}/sound.wav', 'wb') as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((track * 32767).astype(np.int16).tobytes())
vid = glob.glob(f'{outdir}/*.webm')[0]
subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-ss', str(trim), '-i', vid, '-ss', str(trim), '-i', f'{outdir}/sound.wav',
    '-map', '0:v', '-map', '1:a', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '27', '-pix_fmt', 'yuv420p',
    '-vf', 'crop=390:844:0:0,scale=780:1688:flags=lanczos', '-r', '30', '-c:a', 'aac', '-b:a', '96k', '-shortest', '-movflags', '+faststart', dest], check=True)
print('ok', dest)
