"""Telifsiz dini fon müzikleri.

make(..., makam="rast")  -> neşeli, umutlu ilahi havası (varsayılan): Rast makamı, kanun benzeri
                            tıngırtı, ney ezgisi, hafif def ritmi.
make(..., makam="hicaz") -> eski sakin/duygusal versiyon.

Hicaz versiyonu: Hicaz makamında ney benzeri ezgi,
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


def make(path, seconds, varyant=None, makam='rast'):
    if makam == 'rast':
        return make_rast(path, seconds, varyant)
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


# --- Rast: neşeli, "hayırlı olsun" havası -----------------------------------------
# Sol perdesinden Rast: Sol La Si(çeyrek pes) Do Re Mi Fa#(hafif pes) Sol La Si Do Re
RAST = [55, 57, 58.8, 60, 62, 64, 65.8, 67, 69, 70.8, 72, 74]


def kanun(freq, dur, amp=0.22):
    n = int(SR * dur)
    t = np.arange(n) / SR
    s = np.sin(2 * np.pi * freq * t) + 0.5 * np.sin(4 * np.pi * freq * t) + 0.22 * np.sin(6 * np.pi * freq * t)
    return s * np.exp(-t * 5.5) * np.clip(t / 0.004, 0, 1) * amp


def defvur(kind, amp=0.5):
    n = int(SR * 0.35)
    t = np.arange(n) / SR
    if kind == 'dum':
        f = 95 * np.exp(-t * 6) + 55
        s = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 11)
    else:
        rng = np.random.RandomState(5)
        s = rng.normal(0, 1, n) * np.exp(-t * 38) * 0.35 + np.sin(2 * np.pi * 380 * t) * np.exp(-t * 30) * 0.4
    return s * amp


def make_rast(path, seconds, varyant=None):
    rng = np.random.RandomState(zlib.crc32(str(varyant).encode()) % (2 ** 31) if varyant else 21)
    n = int(SR * seconds)
    out = np.zeros(n + SR)
    bpm = 96
    beat = 60 / bpm

    def put(sig, t0):
        i0 = int(t0 * SR)
        if i0 >= len(out):
            return
        out[i0:i0 + len(sig)] += sig[:len(out) - i0]

    # hafif dem: Sol ve Re (majör, aydınlık)
    t = np.arange(len(out)) / SR
    out += (0.05 * np.sin(2 * np.pi * hz(43) * t) + 0.04 * np.sin(2 * np.pi * hz(50) * t)) * np.clip(t / 1.0, 0, 1)

    # def: Sofyan usulü (düm - tek tek), yumuşak
    b = 0
    while b * beat < seconds:
        put(defvur('dum' if b % 4 == 0 else 'tek', 0.45 if b % 4 == 0 else 0.22), b * beat)
        if b % 4 == 2:
            put(defvur('tek', 0.18), (b + 0.5) * beat)
        b += 1

    # kanun: akor arpejleri (Sol - Do - Re - Sol)
    akorlar = [[55, 59, 62, 67], [60, 64, 67, 72], [62, 65.8, 69, 74], [55, 58.8, 62, 67]]
    b = 0
    while b * beat < seconds:
        ak = akorlar[(b // 4) % len(akorlar)]
        for j in range(2):
            put(kanun(hz(ak[(b * 2 + j) % len(ak)]), 0.6, 0.16), (b + j * 0.5) * beat)
        b += 1

    # ney ezgisi: yükselen, sevinçli cümleler; Sol'de karar
    cumleler = [[0, 2, 4, 5, 4, 3, 4, 2, 1, 0], [4, 5, 7, 8, 7, 5, 4, 5, 3, 2, 1, 0], [7, 9, 8, 7, 5, 4, 5, 4, 2, 0]]
    ci = int(rng.randint(0, len(cumleler)))
    tt = 2 * beat
    while tt < seconds - 1.0:
        c = cumleler[ci % len(cumleler)]
        for k, d in enumerate(c):
            dur = beat if k < len(c) - 1 else 2 * beat
            if k % 3 == 2:
                dur = beat / 2
            if tt + dur > seconds - 0.4:
                break
            put(ney(hz(RAST[d] + 12), dur + 0.08, rng, amp=0.2), tt)
            tt += dur
        tt += beat
        ci += 1

    out = reverb(out[:n], sec=1.2, mix=0.18)
    out *= np.clip(np.arange(n) / (SR * 0.4), 0, 1) * np.clip((n - np.arange(n)) / (SR * 1.0), 0, 1)
    out = out / (np.abs(out).max() + 1e-9) * 0.7
    st = np.stack([out, np.roll(out, int(SR * 0.01))], axis=1)
    w = wave.open(path, 'wb')
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes((st * 32767).astype(np.int16).tobytes())
    w.close()


if __name__ == '__main__':
    make(sys.argv[1], float(sys.argv[2]), sys.argv[3] if len(sys.argv) > 3 else None)
