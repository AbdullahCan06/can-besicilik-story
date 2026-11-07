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


def _sentez(path, seconds, varyant=None):
    """varyant verilirse tempo, ton, akor dizisi, melodi ve çalgı rengi değişir (her video farklı müzik)."""
    global BPM, BEAT
    rng = np.random.RandomState(7 if varyant is None else (__import__('zlib').crc32(str(varyant).encode()) % (2 ** 31)))
    np.random.seed(rng.randint(0, 2 ** 31 - 1))
    if varyant is not None:
        BPM = int(rng.choice([100, 106, 112, 116, 120, 126, 132]))
        BEAT = 60 / BPM
        return _make_var(path, seconds, rng)
    BPM = 116
    BEAT = 60 / BPM
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


def _make_var(path, seconds, rng):
    tr = int(rng.randint(-4, 5))                       # ton kaydırma
    progs = [
        [[60, 64, 67], [55, 59, 62], [57, 60, 64], [53, 57, 60]],   # I-V-vi-IV
        [[60, 64, 67], [53, 57, 60], [55, 59, 62], [60, 64, 67]],   # I-IV-V-I
        [[57, 60, 64], [53, 57, 60], [60, 64, 67], [55, 59, 62]],   # vi-IV-I-V
        [[60, 64, 67], [57, 60, 64], [53, 57, 60], [55, 59, 62]],   # I-vi-IV-V
        [[62, 65, 69], [55, 59, 62], [60, 64, 67], [57, 60, 64]],   # ii-V-I-vi
    ]
    chords = [[n + tr for n in c] for c in progs[rng.randint(len(progs))]]
    roots = [c[0] - 24 for c in chords]
    scale = [0, 2, 4, 5, 7, 9, 11]
    bright = float(rng.uniform(0.35, 0.65))
    bell_gain = float(rng.uniform(0.2, 0.32))
    strum2 = rng.rand() < 0.6
    n = int(SR * (seconds + 1))
    mix = np.zeros(n)
    beats = int(seconds / BEAT) + 1
    # 2 ölçülük rastgele melodi motifi, akorlara uyan notalardan
    motif = []
    t = 0.0
    while t < 8:
        d = float(rng.choice([0.5, 0.5, 1.0, 1.0, 1.5]))
        bar = int(t // 4) % 4
        pool = [x + 12 for x in chords[bar]] + [72 + tr + scale[rng.randint(7)]]
        motif.append((t, int(pool[rng.randint(len(pool))]), d))
        t += d
    for b in range(beats):
        bar = (b // 4) % 4
        tt = b * BEAT
        for k, off in enumerate((0, 0.5) if strum2 else (0,)):
            for mm, nn in enumerate(chords[bar]):
                add(mix, pluck(note(nn), BEAT * 1.2, bright), tt + off * BEAT + mm * 0.012, 0.22 if k == 0 else 0.14)
        if b % 2 == 0:
            add(mix, bass(note(roots[bar]), BEAT * 1.8), tt, 0.55)
        add(mix, kick(), tt, 0.7 if b % 2 == 0 else 0.45)
        if b % 2 == 1:
            add(mix, clap(), tt, 0.5)
        add(mix, hat(), tt + BEAT / 2, 1.0)
    for rep in range(0, beats, 8):
        for bt, nn, d in motif:
            add(mix, bell(note(nn), d * BEAT * 1.6), (rep + bt) * BEAT, bell_gain)
    mix = mix[:int(SR * seconds)]
    fi, fo = int(SR * 0.15), int(SR * 1.2)
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


# --- Gerçek kayıtlar -----------------------------------------------------------------
# assets/muzik/ klasörüne telifsiz gerçek müzik dosyaları (mp3/m4a/wav/ogg) konursa
# videolarda bunlar kullanılır; klasör boşsa eski bilgisayar müziğine (_sentez) düşülür.
import os as _os
import subprocess as _sp
import zlib as _zlib

KAYIT_DIR = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), 'assets', 'muzik')


def kayitlar():
    if not _os.path.isdir(KAYIT_DIR):
        return []
    return sorted(_os.path.join(KAYIT_DIR, f) for f in _os.listdir(KAYIT_DIR)
                  if f.lower().endswith(('.mp3', '.m4a', '.wav', '.ogg', '.aac', '.flac')))


def _sure(f):
    return float(_sp.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
                                   '-of', 'csv=p=0', f]).decode().strip())


def make(path, seconds, varyant=None):
    """Gerçek kayıt varsa ondan, yoksa sentezle seconds uzunluğunda stereo 44.1 kHz wav yazar."""
    ks = kayitlar()
    if not ks:
        return _sentez(path, seconds, varyant)
    h = _zlib.crc32(str(varyant).encode()) if varyant else 0
    f = ks[h % len(ks)]
    total = _sure(f)
    bos = max(0.0, total - seconds - 2)
    # parçanın ilk %60'ından deterministik bir başlangıç noktası (her video farklı yer)
    bas = (h // len(ks) % 1000) / 1000 * min(bos, total * 0.6) if bos > 0 else 0.0
    fo = max(0.0, seconds - 1.5)
    af = (f'afade=t=in:st=0:d=0.6,afade=t=out:st={fo:.2f}:d=1.5,'
          f'loudnorm=I=-16:TP=-1.5:LRA=11')
    loop = ['-stream_loop', '-1'] if total < seconds + 0.5 else []
    _sp.run(['ffmpeg', '-y', '-loglevel', 'error'] + loop + ['-ss', f'{bas:.2f}', '-i', f, '-t', f'{seconds:.3f}',
             '-af', af, '-ar', '44100', '-ac', '2', '-c:a', 'pcm_s16le', path], check=True)


if __name__ == '__main__':
    make(sys.argv[1], float(sys.argv[2]))
