"""Telifsiz, neşeli sabah müziği üretir (Karplus-Strong telli + zil melodisi + bas + davul).

Kullanım: python3 muzik.py cikti.wav sure_saniye
"""
import sys
import wave

import numpy as np

SR = 44100
BPM = 116
BEAT = 60 / BPM


def note(n):
    return 440.0 * 2 ** ((n - 69) / 12)


def pluck(freq, dur, bright=0.5):
    n = int(SR * dur)
    p = max(2, int(SR / freq))
    buf = np.random.uniform(-1, 1, p) * 0.5
    out = np.zeros(n)
    for i in range(n):
        out[i] = buf[i % p]
        buf[i % p] = 0.996 * (bright * buf[i % p] + (1 - bright) * buf[(i + 1) % p])
    return out


def bell(freq, dur):
    t = np.arange(int(SR * dur)) / SR
    env = np.exp(-t * 5)
    return env * (np.sin(2 * np.pi * freq * t) + 0.35 * np.sin(2 * np.pi * freq * 2.76 * t) * np.exp(-t * 9))


def bass(freq, dur):
    t = np.arange(int(SR * dur)) / SR
    env = np.minimum(1, t * 80) * np.exp(-t * 3)
    return env * (np.sin(2 * np.pi * freq * t) + 0.3 * np.sin(4 * np.pi * freq * t))


def kick():
    t = np.arange(int(SR * 0.25)) / SR
    f = 120 * np.exp(-t * 25) + 45
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 14)


def clap():
    t = np.arange(int(SR * 0.18)) / SR
    return np.random.uniform(-1, 1, len(t)) * np.exp(-t * 30) * 0.6


def hat():
    t = np.arange(int(SR * 0.05)) / SR
    x = np.random.uniform(-1, 1, len(t))
    x = np.diff(np.concatenate([[0], x]))
    return x * np.exp(-t * 80) * 0.25


def add(track, sig, at, gain=1.0):
    i = int(at * SR)
    if i >= len(track):
        return
    j = min(len(track), i + len(sig))
    track[i:j] += sig[:j - i] * gain


def make(path, seconds):
    np.random.seed(7)
    n = int(SR * (seconds + 1))
    mix = np.zeros(n)
    # Do majör: C – G – Am – F (her akor 2 ölçü değil, 1 ölçü = 4 vuruş)
    chords = [[60, 64, 67], [55, 59, 62], [57, 60, 64], [53, 57, 60]]
    roots = [36, 43, 45, 41]
    melody = [  # (vuruş, nota, süre-vuruş)
        (0, 76, 0.5), (0.5, 79, 0.5), (1, 81, 1), (2, 79, 0.5), (2.5, 76, 0.5), (3, 74, 1),
        (4, 74, 0.5), (4.5, 76, 0.5), (5, 79, 1), (6, 76, 0.5), (6.5, 74, 0.5), (7, 72, 1),
        (8, 72, 0.5), (8.5, 74, 0.5), (9, 76, 1), (10, 79, 0.5), (10.5, 81, 0.5), (11, 79, 1),
        (12, 77, 0.5), (12.5, 76, 0.5), (13, 74, 1), (14, 72, 1), (15, 79, 1),
    ]
    beats = int(seconds / BEAT) + 1
    for b in range(beats):
        bar = (b // 4) % 4
        t = b * BEAT
        # telli çalım: her vuruşta iki kez (yukarı-aşağı)
        for k, off in enumerate((0, 0.5)):
            for m, nn in enumerate(chords[bar]):
                add(mix, pluck(note(nn), BEAT * 1.2, 0.5), t + off * BEAT + m * 0.012, 0.22 if k == 0 else 0.15)
        if b % 2 == 0:
            add(mix, bass(note(roots[bar]), BEAT * 1.8), t, 0.55)
        add(mix, kick(), t, 0.7 if b % 2 == 0 else 0.45)
        if b % 2 == 1:
            add(mix, clap(), t, 0.55)
        add(mix, hat(), t + BEAT / 2, 1.0)
    for rep in range(0, beats, 16):
        if rep < 2:   # ilk iki vuruş girişte melodi yok
            pass
        for bt, nn, d in melody:
            add(mix, bell(note(nn), d * BEAT * 1.6), (rep + bt) * BEAT, 0.28)

    mix = mix[:int(SR * seconds)]
    # giriş/çıkış yumuşatma
    fi, fo = int(SR * 0.15), int(SR * 1.5)
    mix[:fi] *= np.linspace(0, 1, fi)
    mix[-fo:] *= np.linspace(1, 0, fo)
    mix = np.tanh(mix * 1.1)
    mix /= np.max(np.abs(mix)) + 1e-9
    mix *= 0.85
    st = np.stack([mix, np.roll(mix, int(SR * 0.008))], axis=1)
    with wave.open(path, 'wb') as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((st * 32767).astype(np.int16).tobytes())


if __name__ == '__main__':
    make(sys.argv[1], float(sys.argv[2]))
