"""Yumuşak, dini motifli telifsiz fon müziği: Hicaz makamında ney benzeri ezgi,
tanpura benzeri dem (D-A), hafif pad ve yankı. Davul yok.

Kullanım: python3 sakin_muzik.py cikti.wav sure_saniye [varyant]
"""
import sys
import wave
import zlib

import numpy as np

SR = 44100
# Hicaz (Re perdesinden): Re Mi♭ Fa# Sol La Si♭ Do Re  -> MIDI
HICAZ = [62, 63, 66, 67, 69, 70, 72, 74]


def hz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def ney(freq, dur, rng, amp=0.32):
    """Nefesli, vibratolu, yavaş girişli ney benzeri ton."""
    n = int(SR * dur)
    t = np.arange(n) / SR
    vib = 1 + 0.006 * np.sin(2 * np.pi * 5.2 * t) * np.clip(t / 0.6, 0, 1)
    ph = 2 * np.pi * freq * np.cumsum(vib) / SR
    tone = np.sin(ph) + 0.28 * np.sin(2 * ph) + 0.10 * np.sin(3 * ph)
    breath = rng.normal(0, 1, n)
    breath = np.convolve(breath, np.ones(30) / 30, mode='same') * 0.35
    env = np.clip(t / 0.35, 0, 1) * np.clip((dur - t) / 0.45, 0, 1)
    return (tone * (1 + 0.15 * breath) + breath * 0.25) * env * amp


def dem(seconds):
    """Re ve La perdesinde sürekli, yumuşak dem (drone)."""
    n = int(SR * seconds)
    t = np.arange(n) / SR
    s = np.zeros(n)
    for m, a in [(50, 0.16), (57, 0.10), (62, 0.06)]:
        f = hz(m)
        s += a * (np.sin(2 * np.pi * f * t) + 0.3 * np.sin(2 * np.pi * 2 * f * t + 0.4))
    swell = 0.75 + 0.25 * np.sin(2 * np.pi * t / 6.0)
    fade = np.clip(t / 1.5, 0, 1) * np.clip((seconds - t) / 1.5, 0, 1)
    return s * swell * fade


def reverb(x, sec=2.2, mix=0.32, seed=3):
    rng = np.random.RandomState(seed)
    n = int(SR * sec)
    ir = rng.normal(0, 1, n) * np.exp(-np.arange(n) / (SR * sec / 5.5))
    ir /= np.sqrt((ir ** 2).sum())
    wet = np.fft.irfft(np.fft.rfft(x, len(x) + n) * np.fft.rfft(ir, len(x) + n))[:len(x)]
    return (1 - mix) * x + mix * wet


def make(path, seconds, varyant=None):
    rng = np.random.RandomState(zlib.crc32(str(varyant).encode()) % (2 ** 31) if varyant else 11)
    n = int(SR * seconds)
    out = dem(seconds)
    # Ezgi: Hicaz dizisinde, merkez La (5. derece) etrafında dolaşan, Re'de karar veren cümleler
    cumleler = [[4, 5, 4, 3, 2, 1, 0], [4, 6, 5, 4, 3, 2, 3, 1, 0], [0, 1, 2, 3, 4, 3, 2, 1, 0]]
    t = 0.9
    ci = int(rng.randint(0, len(cumleler)))
    while t < seconds - 1.2:
        c = cumleler[ci % len(cumleler)]
        for k, d in enumerate(c):
            dur = 0.9 if k < len(c) - 1 else 1.8
            dur *= 0.85 + 0.3 * rng.rand()
            if t + dur > seconds - 0.6:
                break
            ton = ney(hz(HICAZ[d]), dur + 0.25, rng)
            i0 = int(t * SR)
            out[i0:i0 + len(ton)] += ton[:max(0, n - i0)]
            t += dur
        t += 0.6
        ci += 1
    out = reverb(out)
    out *= np.clip(np.arange(n) / (SR * 0.8), 0, 1) * np.clip((n - np.arange(n)) / (SR * 1.2), 0, 1)
    out = out / (np.abs(out).max() + 1e-9) * 0.6
    st = np.stack([out, np.roll(out, int(SR * 0.012))], axis=1)
    data = (st * 32767).astype(np.int16)
    w = wave.open(path, 'wb')
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes(data.tobytes())
    w.close()


if __name__ == '__main__':
    make(sys.argv[1], float(sys.argv[2]), sys.argv[3] if len(sys.argv) > 3 else None)
