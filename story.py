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


def make(photo, label, headline, body, out, ybias=0.35, xbias=0.5):
    base = cover(Image.open(photo), W, H, ybias, xbias)

    # gradients: soft top, deep green bottom
    grad = Image.new('L', (1, H))
    for y in range(H):
        top = max(0, 1 - y / 420) * 150
        b0 = H * 0.28
        bot = 0 if y < b0 else min(1, (y - b0) / (H * 0.30)) ** 1.2 * 245
        grad.putpixel((0, y), int(max(top, bot)))
    grad = grad.resize((W, H))
    shade = Image.new('RGB', (W, H), GREEN)
    base = Image.composite(shade, base, grad)

    d = ImageDraw.Draw(base)

    # logo: circular, white ring, centered near top (below IG header safe zone)
    L = 230
    logo = Image.open(LOGO).convert('RGB').resize((L, L), Image.LANCZOS)
    mask = Image.new('L', (L * 4, L * 4), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, L * 4, L * 4), fill=255)
    mask = mask.resize((L, L), Image.LANCZOS)
    ring = L + 16
    lx, ly = (W - ring) // 2, 190
    sh = Image.new('L', (W, H), 0)
    ImageDraw.Draw(sh).ellipse((lx - 4, ly + 8, lx + ring + 4, ly + ring + 16), fill=110)
    sh = sh.filter(ImageFilter.GaussianBlur(14))
    base = Image.composite(Image.new('RGB', (W, H), (0, 0, 0)), base, sh)
    d = ImageDraw.Draw(base)
    d.ellipse((lx, ly, lx + ring, ly + ring), fill=CREAM)
    base.paste(logo, (lx + 8, ly + 8), mask)

    # text block, laid out bottom-up so it ends above IG reply bar
    M = 90
    fl = font('Poppins-Medium.ttf', 34)
    fh = font('Poppins-Bold.ttf', 92)
    fb = font('Poppins-Regular.ttf', 40)
    ff = font('Poppins-Medium.ttf', 30)

    hl = wrap(d, headline, fh, W - 2 * M)
    bl = wrap(d, body, fb, W - 2 * M)
    footer = 'KURBAN  •  ADAK  •  AKİKA  •  ŞÜKÜR'

    # heights of each block, laid out top-down so the stack ends at y_end
    PRICE_H = 96
    WA_H = 70
    CHIP_H = 70
    total = (44 + 24 + len(hl) * 104 + 30 + len(bl) * 58 + 36 + PRICE_H + 22 + CHIP_H + 40
             + 4 + 34 + 40 + 36 + WA_H)
    y = 1690 - total

    # label (gold, letter-spaced)
    x = M
    for ch in label.upper():
        d.text((x, y), ch, font=fl, fill=GOLD)
        x += d.textlength(ch, font=fl) + 5
    y += 44 + 24
    for line in hl:
        d.text((M, y), line, font=fh, fill=CREAM); y += 104
    y += 30
    for line in bl:
        d.text((M, y), line, font=fb, fill=(232, 236, 228)); y += 58
    y += 36

    # price pill: struck-through old price + new starting price
    fo = font('Poppins-Medium.ttf', 36)
    fn = font('Poppins-Bold.ttf', 48)
    fs = font('Poppins-Medium.ttf', 32)
    old, new, suf = CFG['eski_fiyat'], CFG['yeni_fiyat'], CFG['fiyat_ek']
    wo, wn, ws = (d.textlength(old, font=fo), d.textlength(new, font=fn),
                  d.textlength(suf, font=fs))
    pw = 36 + wo + 26 + wn + ws + 36
    d.rounded_rectangle((M, y, M + pw, y + PRICE_H), radius=PRICE_H // 2, fill=GOLD)
    cy = y + PRICE_H // 2
    x = M + 36
    d.text((x, cy), old, font=fo, fill=(92, 74, 40), anchor='lm')
    d.line((x - 4, cy + 2, x + wo + 4, cy + 2), fill=(150, 30, 30), width=5)
    x += wo + 26
    d.text((x, cy), new, font=fn, fill=GREEN, anchor='lm')
    x += wn
    d.text((x, cy + 4), suf, font=fs, fill=GREEN, anchor='lm')
    y += PRICE_H + 22

    # feature chips: outlined pills with a check mark
    fc = font('Poppins-Medium.ttf', 32)
    x = M
    for txt in CFG['etiketler']:
        tw = d.textlength(txt, font=fc)
        cw = 26 + 30 + 12 + tw + 28
        d.rounded_rectangle((x, y, x + cw, y + CHIP_H), radius=CHIP_H // 2, outline=GOLD, width=3)
        ccx, ccy = x + 26 + 15, y + CHIP_H // 2
        d.ellipse((ccx - 15, ccy - 15, ccx + 15, ccy + 15), fill=GOLD)
        d.line([(ccx - 8, ccy), (ccx - 2, ccy + 6), (ccx + 8, ccy - 6)], fill=GREEN, width=4, joint='curve')
        d.text((ccx + 15 + 12, ccy + 2), txt, font=fc, fill=CREAM, anchor='lm')
        x += cw + 18
    y += CHIP_H + 40

    d.line((M, y, M + 120, y), fill=GOLD, width=4)
    y += 4 + 34
    d.text((M, y - 4), footer, font=ff, fill=GOLD)
    y += 40 + 36

    # WhatsApp line with a simple chat-bubble mark
    r = 32
    cx, cy = M + r, y + WA_H // 2
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(37, 211, 102))
    d.polygon([(cx - r + 8, cy + r - 14), (cx - r - 4, cy + r + 6), (cx - r + 22, cy + r - 4)],
              fill=(37, 211, 102))
    pf = font('Poppins-Bold.ttf', 26)
    d.text((cx, cy), 'WA', font=pf, fill='white', anchor='mm')
    fw1 = font('Poppins-Regular.ttf', 30)
    fw2 = font('Poppins-Bold.ttf', 50)
    d.text((M + 2 * r + 22, cy - 22), 'WhatsApp sipariş hattı', font=fw1, fill=(232, 236, 228), anchor='lm')
    d.text((M + 2 * r + 22, cy + 18), CFG['whatsapp'], font=fw2, fill=CREAM, anchor='lm')

    base.save(out, quality=92)


if __name__ == '__main__':
    make(*sys.argv[1:6], ybias=float(sys.argv[6]) if len(sys.argv) > 6 else 0.35)
