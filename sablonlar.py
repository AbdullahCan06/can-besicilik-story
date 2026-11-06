"""Farklı görünümlü story/Reels şablonları (şeffaf yazı katmanı, RGBA 1080x1920).

Her şablon aynı bilgileri (logo, kampanya şeridi, başlık, fiyat, WhatsApp) farklı bir düzenle verir:
  sade    : alt bantta yazılar (story.sade_overlay)
  ust     : başlık üstte koyu bantta, altta küçük fiyat + WhatsApp şeridi
  kart    : altta krem renkli yuvarlak kart, koyu yazı
  rozet   : sağ üstte büyük yuvarlak fiyat rozeti, ortada renkli başlık kutusu
  cerceve : renkli çerçeve; fotoğraf/video ortada yuvarlak köşeli pencerede
"""
import math

from PIL import Image, ImageDraw, ImageFilter

import story

W, H = 1080, 1920
F = story.font
SIRA = ['sade', 'ust', 'kart', 'rozet', 'cerceve']
# Hareketli etiketlerin (videoda) dikey merkezi; her şablonda boş kalan yere denk gelir
ETIKET_Y = {'sade': 430, 'ust': 1300, 'kart': 430, 'rozet': 640, 'cerceve': 560}


def _logo(ov, L, x, y, ring=None):
    lg = Image.open(story.LOGO).convert('RGB').resize((L, L), Image.LANCZOS)
    m = Image.new('L', (L * 4, L * 4), 0)
    ImageDraw.Draw(m).ellipse((0, 0, L * 4, L * 4), fill=255)
    m = m.resize((L, L), Image.LANCZOS)
    ImageDraw.Draw(ov).ellipse((x - 6, y - 6, x + L + 6, y + L + 6), fill=(ring or story.CREAM) + (255,))
    ov.paste(lg, (x, y), m)


def _grad(ov, y0, y1, color, a0, a1):
    g = Image.new('L', (1, H), 0)
    for y in range(max(0, y0), min(H, y1)):
        t = (y - y0) / max(1, (y1 - y0))
        g.putpixel((0, y), int(a0 + (a1 - a0) * t))
    ov.paste(Image.new('RGBA', (W, H), color + (255,)), (0, 0), g.resize((W, H)))


def _fit(d, text, name, size, maxw, lines=2, minsize=40):
    return story._fit(d, text, name, size, maxw, lines=lines, minsize=minsize)


def _price(d, x, y, big=64, dark=False):
    fo, fn = F('Poppins-Medium.ttf', int(big * 0.47)), F('Poppins-Bold.ttf', big)
    old, new = story.CFG['eski_fiyat'], story.CFG['yeni_fiyat']
    wo, wn = d.textlength(old, font=fo), d.textlength(new, font=fn)
    ph = big + 32
    pw = 28 + wo + 18 + wn + 28
    d.rounded_rectangle((x, y, x + pw, y + ph), radius=ph // 2, fill=story.GOLD + (255,))
    cy = y + ph / 2
    d.text((x + 28, cy), old, font=fo, fill=(92, 74, 40, 255), anchor='lm')
    d.line((x + 24, cy + 2, x + 32 + wo, cy + 2), fill=(170, 20, 30, 255), width=4)
    d.text((x + 28 + wo + 18, cy + 4), new, font=fn, fill=story.GREEN + (255,), anchor='lm')
    fs = F('Poppins-Medium.ttf', 30)
    a, b = story.CFG['fiyat_ek'].strip().rsplit(' ', 1)
    col = (40, 40, 40, 255) if dark else story.CREAM + (255,)
    d.text((x + pw + 16, cy - 19), a, font=fs, fill=col, anchor='lm')
    d.text((x + pw + 16, cy + 19), b, font=fs, fill=col, anchor='lm')
    return x + pw, y + ph


def _wa(d, x, y, size=44, color=None, anchor='l'):
    txt = 'WhatsApp  ' + story.CFG['whatsapp']
    f = F('Poppins-Bold.ttf', size)
    tw = d.textlength(txt, font=f)
    r = int(size * 0.62)
    total = 2 * r + 14 + tw
    if anchor == 'm':
        x = (W - total) / 2
    cx, cy = x + r, y + r
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(37, 211, 102, 255))
    d.text((cx, cy), 'WA', font=F('Poppins-Bold.ttf', int(size * 0.48)), fill=(255, 255, 255, 255), anchor='mm')
    d.text((x + 2 * r + 14, cy + 2), txt, font=f, fill=(color or story.CREAM) + (255,), anchor='lm')
    return y + 2 * r


def _serit(d, x, y, text, size=32, center=False):
    f = F('Poppins-Bold.ttf', size)
    tw = d.textlength(text, font=f)
    while tw > W - 160 and size > 22:
        size -= 2
        f = F('Poppins-Bold.ttf', size)
        tw = d.textlength(text, font=f)
    h = size + 30
    if center:
        x = (W - tw - 52) / 2
    d.rounded_rectangle((x, y, x + tw + 52, y + h), radius=h // 2, fill=story.RED + (255,),
                        outline=story.GOLD + (255,), width=3)
    d.text((x + 26, y + h / 2 + 2), text, font=f, fill=(255, 255, 255, 255), anchor='lm')
    return y + h


def ust(headline, kamp, hareketli):
    ov = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    _grad(ov, 0, 520, story.GREEN, 250, 235)
    _grad(ov, 520, 900, story.GREEN, 235, 0)
    _grad(ov, H - 330, H, (0, 0, 0), 0, 210)
    d = ImageDraw.Draw(ov)
    _logo(ov, 120, (W - 120) // 2, 90)
    d = ImageDraw.Draw(ov)
    y = 250
    if kamp.get('serit'):
        y = _serit(d, 0, y, kamp['serit'], 30, center=True) + 26
    fh, hl = _fit(d, headline, 'Poppins-Bold.ttf', 84, W - 140, 2, 56)
    for l in hl:
        d.text((W / 2, y), l, font=fh, fill=story.CREAM + (255,), anchor='ma')
        y += int(fh.size * 1.15)
    yb = H - 250
    _price(d, 70, yb, 58)
    _wa(d, 70, yb + 120, 40)
    return ov


def kart(headline, kamp, hareketli):
    ov = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    _grad(ov, 0, 300, (0, 0, 0), 120, 0)
    d = ImageDraw.Draw(ov)
    _logo(ov, 120, 60, 90)
    d = ImageDraw.Draw(ov)
    if kamp.get('serit'):
        _serit(d, 60 + 120 + 26, 90 + 28, kamp['serit'], 28)
    M, cw = 60, W - 120
    fh, hl = _fit(d, headline, 'Poppins-Bold.ttf', 70, cw - 100, 2, 48)
    lh = int(fh.size * 1.15)
    ch = 50 + len(hl) * lh + 24 + 100 + 30 + 60 + 50
    y0 = H - 120 - ch
    sh = Image.new('L', (W, H), 0)
    ImageDraw.Draw(sh).rounded_rectangle((M + 6, y0 + 16, M + cw + 6, y0 + ch + 16), radius=44, fill=110)
    ov.paste(Image.new('RGBA', (W, H), (0, 0, 0, 255)), (0, 0), sh.filter(ImageFilter.GaussianBlur(18)))
    d = ImageDraw.Draw(ov)
    d.rounded_rectangle((M, y0, M + cw, y0 + ch), radius=44, fill=(250, 246, 236, 250))
    d.rectangle((M + 50, y0 + 26, M + 150, y0 + 32), fill=story.GOLD + (255,))
    y = y0 + 50
    for l in hl:
        d.text((M + 50, y), l, font=fh, fill=story.GREEN + (255,))
        y += lh
    y += 24
    _price(d, M + 50, y, 60, dark=True)
    y += 100 + 30
    _wa(d, M + 50, y, 40, color=(30, 30, 30))
    return ov


def rozet(headline, kamp, hareketli):
    ov = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    _grad(ov, 0, 320, (0, 0, 0), 130, 0)
    _grad(ov, H - 420, H, (0, 0, 0), 0, 200)
    d = ImageDraw.Draw(ov)
    _logo(ov, 120, 60, 90)
    # sağ üstte dönük fiyat rozeti
    R = 190
    st = Image.new('RGBA', (2 * R + 40, 2 * R + 40), (0, 0, 0, 0))
    sd = ImageDraw.Draw(st)
    pts = []
    for i in range(48):
        a = math.pi * 2 * i / 48
        rr = R if i % 2 == 0 else R - 16
        pts.append((R + 20 + rr * math.cos(a), R + 20 + rr * math.sin(a)))
    sd.polygon(pts, fill=story.GOLD + (255,))
    sd.ellipse((40, 40, 2 * R, 2 * R), outline=story.RED + (255,), width=6)
    c = R + 20
    sd.text((c, c - 92), story.CFG['eski_fiyat'], font=F('Poppins-Medium.ttf', 34), fill=(110, 80, 40, 255), anchor='mm')
    sd.line((c - 80, c - 90, c + 80, c - 90), fill=(170, 20, 30, 255), width=5)
    sd.text((c, c - 10), story.CFG['yeni_fiyat'], font=F('Poppins-Bold.ttf', 74), fill=story.GREEN + (255,), anchor='mm')
    sd.text((c, c + 66), "'den başlayan", font=F('Poppins-Medium.ttf', 30), fill=(60, 50, 30, 255), anchor='mm')
    sd.text((c, c + 102), 'fiyatlarla', font=F('Poppins-Medium.ttf', 30), fill=(60, 50, 30, 255), anchor='mm')
    st = st.rotate(-12, resample=Image.BICUBIC)
    ov.alpha_composite(st, (W - st.width - 30, 60))
    d = ImageDraw.Draw(ov)
    # alt: başlık kutusu + şerit + WhatsApp
    fh, hl = _fit(d, headline, 'Poppins-Bold.ttf', 72, W - 200, 2, 48)
    lh = int(fh.size * 1.15)
    bh = 40 + len(hl) * lh + 20
    y0 = H - 230 - bh
    d.rounded_rectangle((50, y0, W - 50, y0 + bh), radius=26, fill=story.GREEN + (235,))
    d.rectangle((50, y0, 66, y0 + bh), fill=story.GOLD + (255,))
    y = y0 + 22
    for l in hl:
        d.text((100, y), l, font=fh, fill=story.CREAM + (255,))
        y += lh
    if kamp.get('serit'):
        _serit(d, 50, y0 - 82, kamp['serit'], 28)
    _wa(d, 0, H - 180, 46, anchor='m')
    return ov


def cerceve(headline, kamp, hareketli):
    """Renkli çerçeve; ortadaki pencere şeffaf (fotoğraf/video orada görünür)."""
    ov = Image.new('RGBA', (W, H), story.GREEN + (255,))
    d = ImageDraw.Draw(ov)
    # ince desen: köşelerde altın çizgiler
    for i in range(0, W, 60):
        d.line((i, 0, i + 30, 30), fill=story.GOLD + (60,), width=2)
    top, bot, side = 400, 470, 50
    m = Image.new('L', (W, H), 255)
    ImageDraw.Draw(m).rounded_rectangle((side, top, W - side, H - bot), radius=48, fill=0)
    ov.putalpha(m)
    d = ImageDraw.Draw(ov)
    d.rounded_rectangle((side - 6, top - 6, W - side + 6, H - bot + 6), radius=52, outline=story.GOLD + (255,), width=6)
    _logo(ov, 110, 60, 60)
    d = ImageDraw.Draw(ov)
    d.text((190, 92), 'CAN BESİCİLİK', font=F('Poppins-Bold.ttf', 34), fill=story.GOLD + (255,))
    d.text((190, 134), 'Adak • Akika • Şükür', font=F('Poppins-Medium.ttf', 28), fill=story.CREAM + (255,))
    fh, hl = _fit(d, headline, 'Poppins-Bold.ttf', 76, W - 120, 2, 50)
    y = 210 if len(hl) == 2 else 250
    for l in hl:
        d.text((60, y), l, font=fh, fill=story.CREAM + (255,))
        y += int(fh.size * 1.12)
    if kamp.get('serit'):
        _serit(d, 0, top + 24, kamp['serit'], 28, center=True)
    yb = H - bot + 40
    _price(d, 60, yb, 64)
    _wa(d, 60, yb + 140, 44)
    return ov


def _sabit_etiketler(ov, yc):
    """Fotoğraflı (hareketsiz) story'de hizmet bilgilerini küçük etiketler halinde yazar."""
    d = ImageDraw.Draw(ov)
    f = F('Poppins-SemiBold.ttf' if False else 'Poppins-Bold.ttf', 30)
    items = story.CFG['etiketler']
    rows, cur, curw = [], [], 0
    for t in items:
        w = d.textlength(t, font=f) + 70
        if cur and curw + w + 14 > W - 120:
            rows.append(cur)
            cur, curw = [], 0
        cur.append((t, w))
        curw += w + 14
    rows.append(cur)
    h = 58
    y = yc - (len(rows) * (h + 12)) // 2
    for row in rows:
        tot = sum(w for _, w in row) + 14 * (len(row) - 1)
        x = (W - tot) / 2
        for t, w in row:
            d.rounded_rectangle((x, y, x + w, y + h), radius=h // 2, fill=(0, 0, 0, 150),
                                outline=story.GOLD + (255,), width=3)
            d.ellipse((x + 14, y + 15, x + 42, y + 43), fill=story.GOLD + (255,))
            d.line([(x + 21, y + 29), (x + 27, y + 35), (x + 36, y + 23)], fill=story.GREEN + (255,), width=4)
            d.text((x + 52, y + h / 2 + 1), t, font=f, fill=(255, 255, 255, 255), anchor='lm')
            x += w + 14
        y += h + 12
    return ov


def overlay(ad, headline, v=None, tema=None, hareketli=True):
    if tema:
        story.set_tema(tema)
    if ad == 'sade':
        return story.sade_overlay(headline, v, tema, hareketli=hareketli)
    kamp = story.variant(v)
    ov = {'ust': ust, 'kart': kart, 'rozet': rozet, 'cerceve': cerceve}[ad](headline, kamp, hareketli)
    if not hareketli:
        _sabit_etiketler(ov, ETIKET_Y[ad])
    return ov


def sec(k):
    """k. paylaşım için şablon adı (ayarlar.json 'sablonlar' listesiyle sırayla döner)."""
    lst = story.CFG.get('sablonlar') or SIRA
    return lst[k % len(lst)]
