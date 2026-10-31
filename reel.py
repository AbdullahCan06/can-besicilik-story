"""Fotoğraflardan Reels videosu (1080x1920, 30 fps, yavaş yakınlaşma + yazı + kapanış kartı).

reels/<ad>.json dosyasındaki tanımdan reels/<ad>.mp4 üretir:
{"slaytlar": [["foto04.jpg", "Üst yazı", "Büyük başlık"], ...],
 "kapanis": ["foto17.jpg", "Etiket", "Başlık", "Metin"]}
"""
import json
import os
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageOps

import story

ROOT = os.path.dirname(os.path.abspath(__file__))
W, H, FPS = 1080, 1920, 30
SLIDE, LAST, FADE = 3.2, 4.0, 0.5
GREEN, GOLD, CREAM = story.GREEN, story.GOLD, story.CREAM


def overlay(top, head):
    """Şeffaf yazı katmanı: üstte logo, ortanın altında yeşil bant üzerinde yazı."""
    ov = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    # alt kısım yeşil geçiş
    grad = Image.new('L', (1, H))
    for y in range(H):
        a = 0 if y < H * 0.45 else min(1, (y - H * 0.45) / (H * 0.30)) ** 1.2 * 225
        a = max(a, max(0, 1 - y / 360) * 120)
        grad.putpixel((0, y), int(a))
    ov.paste(Image.new('RGBA', (W, H), GREEN + (255,)), (0, 0), grad.resize((W, H)))
    d = ImageDraw.Draw(ov)

    L = 170
    logo = Image.open(story.LOGO).convert('RGB').resize((L, L), Image.LANCZOS)
    m = Image.new('L', (L * 4, L * 4), 0)
    ImageDraw.Draw(m).ellipse((0, 0, L * 4, L * 4), fill=255)
    m = m.resize((L, L), Image.LANCZOS)
    lx, ly = (W - L - 12) // 2, 170
    d.ellipse((lx, ly, lx + L + 12, ly + L + 12), fill=CREAM + (255,))
    ov.paste(logo, (lx + 6, ly + 6), m)

    M = 90
    fh = story.font('Poppins-Bold.ttf', 96)
    ft = story.font('Poppins-Medium.ttf', 38)
    hl = story.wrap(d, head, fh, W - 2 * M - 120)
    y = 1180 - (len(hl) - 1) * 108
    x = M
    for ch in top.upper():
        d.text((x, y), ch, font=ft, fill=GOLD + (255,))
        x += d.textlength(ch, font=ft) + 5
    y += 64
    for line in hl:
        d.text((M, y), line, font=fh, fill=CREAM + (255,))
        y += 108
    d.line((M, y + 18, M + 120, y + 18), fill=GOLD + (255,), width=5)
    d.text((M, y + 50), 'WhatsApp: ' + story.CFG['whatsapp'], font=story.font('Poppins-Medium.ttf', 40),
           fill=CREAM + (255,))
    return ov


def base_photo(path, xbias, ybias, scale=1.12):
    im = ImageOps.exif_transpose(Image.open(path)).convert('RGB')
    return story.cover(im, int(W * scale), int(H * scale), ybias, xbias)


def slide_frames(path, xbias, ybias, top, head, n, zoom_in=True):
    big = base_photo(path, xbias, ybias)
    ov = overlay(top, head)
    BW, BH = big.size
    for i in range(n):
        t = i / max(1, n - 1)
        z = (1 - t) if zoom_in else t           # 1 -> tüm görüntü, 0 -> en yakın
        cw = int(W + (BW - W) * z)
        ch = int(H + (BH - H) * z)
        x0 = (BW - cw) // 2
        y0 = (BH - ch) // 2
        fr = big.crop((x0, y0, x0 + cw, y0 + ch)).resize((W, H), Image.BILINEAR).convert('RGBA')
        fr.alpha_composite(ov)
        yield np.asarray(fr.convert('RGB'))


def build(name):
    spec = json.load(open(os.path.join(ROOT, 'reels', name + '.json'), encoding='utf-8'))
    crop = story.CFG['kirpma']
    seq = []
    for k, (photo, top, head) in enumerate(spec['slaytlar']):
        xb, yb = crop.get(photo, [0.5, 0.35])
        seq.append(list(slide_frames(os.path.join(ROOT, 'fotograflar', photo), xb, yb, top, head,
                                     int(SLIDE * FPS), zoom_in=(k % 2 == 0))))
    photo, lab, head, body = spec['kapanis']
    xb, yb = crop.get(photo, [0.5, 0.35])
    endp = os.path.join(ROOT, 'reels', name + '_kapanis.jpg')
    story.make(os.path.join(ROOT, 'fotograflar', photo), lab, head, body, endp, ybias=yb, xbias=xb)
    end = np.asarray(Image.open(endp).convert('RGB'))
    seq.append([end] * int(LAST * FPS))

    out = os.path.join(ROOT, 'reels', name + '.mp4')
    p = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24',
                          '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                          '-f', 'lavfi', '-i', 'anullsrc=r=44100:cl=stereo', '-shortest',
                          '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '20', '-pix_fmt', 'yuv420p',
                          '-c:a', 'aac', '-b:a', '128k', '-movflags', '+faststart', out],
                         stdin=subprocess.PIPE)
    nf = int(FADE * FPS)
    for k, frames in enumerate(seq):
        body_frames = frames if k == len(seq) - 1 else frames[:-nf]
        start = nf if k > 0 else 0
        if k > 0:
            prev = seq[k - 1][-nf:]
            for i in range(nf):
                a = (i + 1) / (nf + 1)
                p.stdin.write((prev[i] * (1 - a) + frames[i] * a).astype(np.uint8).tobytes())
        for fr in body_frames[start:]:
            p.stdin.write(fr.tobytes())
    p.stdin.close()
    p.wait()
    print(out, file=sys.stderr)


if __name__ == '__main__':
    for n in sys.argv[1:]:
        build(n)
