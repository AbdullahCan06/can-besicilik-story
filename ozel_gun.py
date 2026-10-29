"""Özel gün görseli: 29 Ekim Cumhuriyet Bayramı (story 1080x1920 ve gönderi 1080x1350)."""
import math
import os
import sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = os.path.dirname(os.path.abspath(__file__))
FD = os.path.join(ROOT, 'assets', 'fonts') + os.sep
LOGO = os.path.join(ROOT, 'assets', 'logo.jpg')
RED = (227, 10, 23)
DARK = (150, 6, 16)
WHITE = (255, 255, 255)
SOFT = (255, 228, 228)


def font(name, size):
    return ImageFont.truetype(FD + name, size)


def flag(G, S=4):
    """Türk bayrağı (TS 2.7 oranları), G = yükseklik; S = süper örnekleme."""
    g = G * S
    w = int(g * 1.5)
    im = Image.new('RGBA', (w, g), RED + (255,))
    d = ImageDraw.Draw(im)
    cy = g / 2
    ax = 0.5 * g
    r1 = 0.25 * g
    d.ellipse((ax - r1, cy - r1, ax + r1, cy + r1), fill=WHITE)
    bx = ax + g / 16
    r2 = 0.2 * g
    d.ellipse((bx - r2, cy - r2, bx + r2, cy + r2), fill=RED)
    sr = 0.125 * g
    sx = bx + r2 + g / 3 + sr
    pts = []
    for i in range(10):
        ang = math.pi + i * math.pi / 5      # ilk uç gönderden (sol) yana bakar
        rr = sr if i % 2 == 0 else sr * 0.382
        pts.append((sx + rr * math.cos(ang), cy + rr * math.sin(ang)))
    d.polygon(pts, fill=WHITE)
    return im.resize((w // S, G), Image.LANCZOS)


def round_logo(L):
    logo = Image.open(LOGO).convert('RGB').resize((L, L), Image.LANCZOS)
    m = Image.new('L', (L * 4, L * 4), 0)
    ImageDraw.Draw(m).ellipse((0, 0, L * 4, L * 4), fill=255)
    return logo, m.resize((L, L), Image.LANCZOS)


def background(W, H):
    bg = Image.new('RGB', (W, H))
    d = ImageDraw.Draw(bg)
    for y in range(H):
        t = y / H
        c = tuple(int(RED[i] * (1 - t) + DARK[i] * t) for i in range(3))
        d.line((0, y, W, y), fill=c)
    # büyük, silik hilal-yıldız filigranı
    wm = flag(int(H * 0.75)).convert('RGBA')
    px = wm.load()
    for yy in range(wm.height):
        for xx in range(wm.width):
            r, g, b, a = px[xx, yy]
            px[xx, yy] = (255, 255, 255, 22 if r > 240 and g > 240 else 0)
    bg.paste(wm, (int(W * 0.42), int(H * 0.30)), wm)
    return bg


def centered(d, y, text, f, fill, W):
    d.text((W // 2, y), text, font=f, fill=fill, anchor='mt')


def make(W, H, out, top=None, _measure=False):
    im = background(W, H)
    d = ImageDraw.Draw(im)
    story = H > 1500
    if top is None:
        h = make(W, H, None, top=0, _measure=True)
        top = max(200 if story else 50, (H - h) // 2 - (20 if story else 0))

    # logo
    L = 210 if story else 130
    logo, m = round_logo(L)
    ring = L + 12
    lx = (W - ring) // 2
    d.ellipse((lx, top, lx + ring, top + ring), fill=WHITE)
    im.paste(logo, (lx + 6, top + 6), m)
    y = top + ring + (70 if story else 40)

    # bayrak, gölgeli
    G = 360 if story else 230
    fl = flag(G)
    fx = (W - fl.width) // 2
    sh = Image.new('L', (W, H), 0)
    ImageDraw.Draw(sh).rectangle((fx + 8, y + 16, fx + fl.width + 8, y + G + 16), fill=120)
    sh = sh.filter(ImageFilter.GaussianBlur(18))
    im = Image.composite(Image.new('RGB', (W, H), (60, 0, 5)), im, sh)
    d = ImageDraw.Draw(im)
    d.rectangle((fx - 6, y - 6, fx + fl.width + 6, y + G + 6), fill=WHITE)
    im.paste(fl, (fx, y), fl)
    y += G + (90 if story else 55)

    centered(d, y, '29 EKİM', font('Poppins-Bold.ttf', 170 if story else 130), WHITE, W)
    y += 190 if story else 145
    centered(d, y, 'CUMHURİYET BAYRAMI', font('Poppins-Medium.ttf', 52 if story else 42), SOFT, W)
    y += 100 if story else 75
    d.line((W // 2 - 60, y, W // 2 + 60, y), fill=WHITE, width=4)
    y += 50 if story else 35
    fb = font('Poppins-Regular.ttf', 44 if story else 36)
    for line in ('Cumhuriyetimizin 103. yılı', 'kutlu olsun.'):
        centered(d, y, line, fb, WHITE, W)
        y += 62 if story else 50
    y += 30 if story else 20
    centered(d, y, 'Can Besicilik ailesi olarak', font('Poppins-Regular.ttf', 34 if story else 28), SOFT, W)
    y += 50 if story else 40
    centered(d, y, 'bayramınızı en içten dileklerimizle kutlarız.',
             font('Poppins-Regular.ttf', 34 if story else 28), SOFT, W)
    y += 50 if story else 40
    if _measure:
        return y
    im.save(out, quality=93)


if __name__ == '__main__':
    os.makedirs(os.path.join(ROOT, 'ozel'), exist_ok=True)
    make(1080, 1920, os.path.join(ROOT, 'ozel', '2026-10-29-story.jpg'))
    make(1080, 1350, os.path.join(ROOT, 'ozel', '2026-10-29-gonderi.jpg'))
