"""Can Besicilik story generator: 1080x1920 story from a photo + headline + body."""
import json
import os
import sys
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageFilter

ROOT = os.path.dirname(os.path.abspath(__file__))
CFG = json.load(open(os.path.join(ROOT, 'ayarlar.json'), encoding='utf-8'))

W, H = 1080, 1920
GREEN = (16, 66, 44)
GOLD = (214, 178, 104)
CREAM = (248, 243, 230)
RED = (200, 16, 46)

# Renk temaları: (zemin rengi, vurgu rengi, kampanya şeridi rengi)
TEMALAR = {
    'yesil':   ((16, 66, 44), (214, 178, 104), (200, 16, 46)),
    'bordo':   ((92, 14, 28), (230, 186, 100), (20, 20, 20)),
    'lacivert': ((16, 36, 72), (240, 190, 80), (200, 16, 46)),
    'kahve':   ((70, 44, 24), (236, 196, 120), (176, 30, 36)),
    'siyah':   ((18, 18, 18), (226, 182, 92), (200, 16, 46)),
    'zeytin':  ((58, 70, 30), (240, 210, 130), (170, 24, 40)),
}
TEMA_SIRASI = ['yesil', 'bordo', 'lacivert', 'kahve', 'siyah', 'zeytin']


def set_tema(ad):
    global GREEN, GOLD, RED
    GREEN, GOLD, RED = TEMALAR.get(ad or 'yesil', TEMALAR['yesil'])
FD = os.path.join(ROOT, 'assets', 'fonts') + os.sep
LOGO = os.path.join(ROOT, 'assets', 'logo.jpg')


def font(name, size):
    return ImageFont.truetype(FD + name, size)


def cover(im, w, h, ybias=0.35, xbias=0.5):
    im = ImageOps.exif_transpose(im).convert('RGB')
    s = max(w / im.width, h / im.height)
    im = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
    x = int((im.width - w) * xbias)
    y = int((im.height - h) * ybias)
    return im.crop((x, y, x + w, y + h))


def wrap(draw, text, f, maxw):
    lines, cur = [], ''
    for word in text.split():
        t = (cur + ' ' + word).strip()
        if draw.textlength(t, font=f) <= maxw:
            cur = t
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def logo_disc(base, L, ly):
    logo = Image.open(LOGO).convert('RGB').resize((L, L), Image.LANCZOS)
    mask = Image.new('L', (L * 4, L * 4), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, L * 4, L * 4), fill=255)
    mask = mask.resize((L, L), Image.LANCZOS)
    ring = L + 14
    lx = (W - ring) // 2
    sh = Image.new('L', (W, H), 0)
    ImageDraw.Draw(sh).ellipse((lx - 4, ly + 8, lx + ring + 4, ly + ring + 16), fill=110)
    sh = sh.filter(ImageFilter.GaussianBlur(14))
    base = Image.composite(Image.new('RGB', (W, H), (0, 0, 0)), base, sh)
    d = ImageDraw.Draw(base)
    d.ellipse((lx, ly, lx + ring, ly + ring), fill=CREAM)
    base.paste(logo, (lx + 7, ly + 7), mask)
    return base, ly + ring


def ribbon(d, y, text, size=40):
    """Kırmızı kampanya şeridi (ortalı)."""
    f = font('Poppins-Bold.ttf', size)
    tw = d.textlength(text, font=f)
    h = size + 40
    x0 = (W - tw) / 2 - 36
    d.rounded_rectangle((x0, y, x0 + tw + 72, y + h), radius=18, fill=RED, outline=GOLD, width=4)
    d.text((W / 2, y + h / 2 + 2), text, font=f, fill=(255, 255, 255), anchor='mm')
    return y + h


def check(d, cx, cy, r=15, fill=None):
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=fill or GOLD)
    k = r / 15
    d.line([(cx - 8 * k, cy), (cx - 2 * k, cy + 6 * k), (cx + 8 * k, cy - 6 * k)], fill=GREEN,
           width=max(3, int(4 * k)), joint='curve')


def chips(d, x0, y, maxw, items, fc, h=62, gap=14, draw=True):
    """Onay işaretli etiketler; sığmazsa alt satıra geçer. Bitiş y değerini döndürür."""
    x = x0
    rows = 1
    for txt in items:
        cw = 22 + 26 + 10 + d.textlength(txt, font=fc) + 24
        if x > x0 and x + cw > x0 + maxw:
            x = x0
            y += h + gap
            rows += 1
        if draw:
            d.rounded_rectangle((x, y, x + cw, y + h), radius=h // 2, outline=GOLD, width=3)
            check(d, x + 22 + 13, y + h / 2, 13)
            d.text((x + 22 + 26 + 10, y + h / 2 + 2), txt, font=fc, fill=CREAM, anchor='lm')
        x += cw + gap
    return y + h


def price_block(d, x, y, big=84):
    """Üstü çizili eski fiyat + büyük yeni fiyat kutusu ve yanında 'den başlayan fiyatlarla'."""
    fo = font('Poppins-Medium.ttf', 36)
    fn = font('Poppins-Bold.ttf', big)
    fs = font('Poppins-Medium.ttf', 34)
    old, new = CFG['eski_fiyat'], CFG['yeni_fiyat']
    wo, wn = d.textlength(old, font=fo), d.textlength(new, font=fn)
    PH = big + 40
    pw = 34 + wo + 24 + wn + 34
    d.rounded_rectangle((x, y, x + pw, y + PH), radius=26, fill=GOLD)
    cy = y + PH / 2
    xx = x + 34
    d.text((xx, cy), old, font=fo, fill=(92, 74, 40), anchor='lm')
    d.line((xx - 4, cy + 2, xx + wo + 4, cy + 2), fill=(170, 20, 30), width=5)
    xx += wo + 24
    d.text((xx, cy + 4), new, font=fn, fill=GREEN, anchor='lm')
    sx = x + pw + 20
    suf = CFG['fiyat_ek'].strip()
    parts = suf.rsplit(' ', 1) if ' ' in suf else [suf, '']
    d.text((sx, cy - 22), parts[0], font=fs, fill=CREAM, anchor='lm')
    d.text((sx, cy + 22), parts[1], font=fs, fill=CREAM, anchor='lm')
    return y + PH


def make(photo, label, headline, body, out, ybias=0.35, xbias=0.5, tema=None):
    set_tema(tema)
    kamp = CFG.get('kampanya') or {}
    base = cover(Image.open(photo), W, H, ybias, xbias)

    b0 = H * (0.20 if kamp else 0.28)
    grad = Image.new('L', (1, H))
    for y in range(H):
        top = max(0, 1 - y / 520) * 170
        bot = 0 if y < b0 else min(1, (y - b0) / (H * 0.24)) ** 1.2 * 248
        grad.putpixel((0, y), int(max(top, bot)))
    grad = grad.resize((W, H))
    base = Image.composite(Image.new('RGB', (W, H), GREEN), base, grad)

    base, ly = logo_disc(base, 170 if kamp else 230, 175)
    d = ImageDraw.Draw(base)
    if kamp.get('serit'):
        ribbon(d, ly + 22, kamp['serit'])

    M = 72
    fl = font('Poppins-Medium.ttf', 32)
    fh = font('Poppins-Bold.ttf', 80)
    fu = font('Poppins-SemiBold.ttf' if os.path.exists(FD + 'Poppins-SemiBold.ttf') else 'Poppins-Bold.ttf', 36)
    fc = font('Poppins-Medium.ttf', 30)
    ft = font('Poppins-Medium.ttf', 33)
    fb = font('Poppins-Regular.ttf', 38)

    hl = wrap(d, headline, fh, W - 2 * M)
    ul = wrap(d, kamp['uyari'], fu, W - 2 * M) if kamp.get('uyari') else []
    bl = [] if kamp else wrap(d, body, fb, W - 2 * M)
    guven = kamp.get('guven', [])
    chip_end = chips(d, M, 0, W - 2 * M, CFG['etiketler'], fc, draw=False)
    WA_H = 70
    total = (40 + 16 + len(hl) * 92 + 18 + len(bl) * 54 + len(ul) * 48 + 26 + 124 + 24 + chip_end + 22
             + len(guven) * 50 + 14 + WA_H)
    y = 1700 - total

    x = M
    for ch in label.upper():
        d.text((x, y), ch, font=fl, fill=GOLD)
        x += d.textlength(ch, font=fl) + 5
    y += 40 + 16
    for line in hl:
        d.text((M, y), line, font=fh, fill=CREAM); y += 92
    y += 18
    for line in bl:
        d.text((M, y), line, font=fb, fill=(232, 236, 228)); y += 54
    for line in ul:
        d.text((M, y), line, font=fu, fill=(255, 214, 120)); y += 48
    y += 26
    y = price_block(d, M, y) + 24
    y = chips(d, M, y, W - 2 * M, CFG['etiketler'], fc) + 22
    for t in guven:
        check(d, M + 15, y + 22, 15)
        d.text((M + 44, y + 24), t, font=ft, fill=CREAM, anchor='lm')
        y += 50
    y += 14

    r = 32
    cx, cy = M + r, y + WA_H // 2
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(37, 211, 102))
    d.polygon([(cx - r + 8, cy + r - 14), (cx - r - 4, cy + r + 6), (cx - r + 22, cy + r - 4)],
              fill=(37, 211, 102))
    d.text((cx, cy), 'WA', font=font('Poppins-Bold.ttf', 26), fill='white', anchor='mm')
    d.text((M + 2 * r + 22, cy - 22), 'WhatsApp sipariş hattı', font=font('Poppins-Regular.ttf', 30),
           fill=(232, 236, 228), anchor='lm')
    d.text((M + 2 * r + 22, cy + 18), CFG['whatsapp'], font=font('Poppins-Bold.ttf', 50), fill=CREAM,
           anchor='lm')

    base.save(out, quality=92)


if __name__ == '__main__':
    make(*sys.argv[1:6], ybias=float(sys.argv[6]) if len(sys.argv) > 6 else 0.35)
