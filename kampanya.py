"""Video story için kampanya yazı katmanları (üst ve alt, ayrı PNG; videoda ayrı ayrı belirir)."""
import os
import sys
from PIL import Image, ImageDraw

import story

W, H = 1080, 1920
GREEN, GOLD, CREAM = story.GREEN, story.GOLD, story.CREAM
RED = (200, 16, 46)
f = story.font


def grad_layer(y0, y1, a0, a1, p=1.0):
    g = Image.new('L', (1, H), 0)
    for y in range(H):
        if y0 <= y <= y1:
            t = ((y - y0) / max(1, y1 - y0)) ** p
            g.putpixel((0, y), int(a0 + (a1 - a0) * t))
    lay = Image.new('RGBA', (W, H), GREEN + (0,))
    lay.putalpha(g.resize((W, H)))
    return lay


def top_layer():
    im = grad_layer(0, 900, 245, 0, p=2.2)
    d = ImageDraw.Draw(im)
    L = 150
    logo = Image.open(story.LOGO).convert('RGB').resize((L, L), Image.LANCZOS)
    m = Image.new('L', (L * 4, L * 4), 0)
    ImageDraw.Draw(m).ellipse((0, 0, L * 4, L * 4), fill=255)
    m = m.resize((L, L), Image.LANCZOS)
    lx, ly = (W - L - 10) // 2, 175
    d.ellipse((lx, ly, lx + L + 10, ly + L + 10), fill=CREAM + (255,))
    im.paste(logo, (lx + 5, ly + 5), m)

    y = 375
    lab = 'BU HAFTA SONU'
    fl = f('Poppins-Bold.ttf', 40)
    tw = sum(d.textlength(c, font=fl) + 8 for c in lab) - 8
    x = (W - tw) / 2
    for c in lab:
        d.text((x, y), c, font=fl, fill=GOLD + (255,))
        x += d.textlength(c, font=fl) + 8
    y += 70
    fh = f('Poppins-Bold.ttf', 112)
    for line in ('Adak kesmeyen', 'kalmasın!'):
        d.text((W // 2 + 4, y + 5), line, font=fh, fill=(0, 30, 15, 150), anchor='mt')
        d.text((W // 2, y), line, font=fh, fill=CREAM + (255,), anchor='mt')
        y += 125
    y += 18
    fs = f('Poppins-Medium.ttf', 40)
    for line in ('En uygun fiyata adaklık satışımız', 'bugün de devam ediyor.'):
        d.text((W // 2, y), line, font=fs, fill=CREAM + (255,), anchor='mt')
        y += 54
    return im


def bottom_layer():
    im = grad_layer(1060, 1250, 0, 245)
    im.alpha_composite(grad_layer(1250, H, 245, 250).crop((0, 1250, W, H)), (0, 1250))
    d = ImageDraw.Draw(im)
    M = 80
    y = 1190
    # fiyat şeridi
    fy, fn, fsuf = f('Poppins-Medium.ttf', 36), f('Poppins-Bold.ttf', 60), f('Poppins-Medium.ttf', 36)
    a, b, c = 'Yalnızca ', story.CFG['yeni_fiyat'], "'den başlayan fiyatlar"
    wa, wb, wc = d.textlength(a, font=fy), d.textlength(b, font=fn), d.textlength(c, font=fsuf)
    pw = 40 + wa + wb + wc + 40
    PH = 100
    px = (W - pw) / 2
    d.rounded_rectangle((px, y, px + pw, y + PH), radius=PH // 2, fill=GOLD + (255,))
    cy = y + PH / 2
    x = px + 40
    d.text((x, cy + 4), a, font=fy, fill=GREEN + (255,), anchor='lm'); x += wa
    d.text((x, cy), b, font=fn, fill=GREEN + (255,), anchor='lm'); x += wb
    d.text((x, cy + 4), c, font=fsuf, fill=GREEN + (255,), anchor='lm')
    y += PH + 26
    d.text((W // 2, y), 'Adak  •  Şükür  •  Akika kurbanı', font=f('Poppins-Medium.ttf', 40),
           fill=CREAM + (255,), anchor='mt')
    y += 76
    # özel indirim rozeti
    fb1, fb2 = f('Poppins-Medium.ttf', 34), f('Poppins-Bold.ttf', 46)
    t1, t2 = 'Birden fazla alımda', 'ÖZEL İNDİRİM'
    bw = max(d.textlength(t1, font=fb1), d.textlength(t2, font=fb2)) + 90
    BH = 128
    bx = (W - bw) / 2
    d.rounded_rectangle((bx, y, bx + bw, y + BH), radius=26, fill=RED + (255,), outline=GOLD + (255,), width=4)
    d.text((W // 2, y + 16), t1, font=fb1, fill=(255, 235, 235, 255), anchor='mt')
    d.text((W // 2, y + 58), t2, font=fb2, fill=(255, 255, 255, 255), anchor='mt')
    y += BH + 30
    d.text((W // 2, y), 'Hemen arayın, yerimize bekleriz!', font=f('Poppins-Bold.ttf', 44),
           fill=CREAM + (255,), anchor='mt')
    y += 70
    # telefon
    fp = f('Poppins-Bold.ttf', 70)
    num = story.CFG['whatsapp']
    nw = d.textlength(num, font=fp)
    r = 36
    gx = (W - (2 * r + 22 + nw)) / 2
    cyy = y + 44
    d.ellipse((gx, cyy - r, gx + 2 * r, cyy + r), fill=(37, 211, 102, 255))
    d.text((gx + r, cyy), 'WA', font=f('Poppins-Bold.ttf', 28), fill=(255, 255, 255, 255), anchor='mm')
    d.text((gx + 2 * r + 22, cyy + 4), num, font=fp, fill=(255, 255, 255, 255), anchor='lm')
    y += 104
    # etiketler
    fc = f('Poppins-Medium.ttf', 32)
    tags = story.CFG['etiketler']
    ws = [d.textlength(t, font=fc) + 56 for t in tags]
    x = (W - (sum(ws) + 18 * (len(ws) - 1))) / 2
    for t, w in zip(tags, ws):
        d.rounded_rectangle((x, y, x + w, y + 62), radius=31, outline=GOLD + (255,), width=3)
        d.text((x + w / 2, y + 33), t, font=fc, fill=CREAM + (255,), anchor='mm')
        x += w + 18
    return im


if __name__ == '__main__':
    out = sys.argv[1]
    top_layer().save(out + '_ust.png')
    bottom_layer().save(out + '_alt.png')
