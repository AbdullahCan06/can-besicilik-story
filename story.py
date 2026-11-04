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


def variant(v):
    """Kampanya metinlerinden v'ye göre farklı bir kombinasyon seçer."""
    k = dict(CFG.get('kampanya') or {})
    if not k:
        return k
    if v is None:
        return k
    if k.get('seritler'):
        k['serit'] = k['seritler'][v % len(k['seritler'])]
    if k.get('uyarilar'):
        k['uyari'] = k['uyarilar'][(v * 3 + 1) % len(k['uyarilar'])]
    gh = k.get('guven_havuz')
    if gh:
        a = (v * 2) % len(gh)
        k['guven'] = [gh[a], gh[(a + 1 + v % 3) % len(gh)]] if len(gh) > 2 else gh
    return k


# ---------------------------------------------------------------------------
# Sade şablon (ayarlar.json "sablon": "sade"): fotoğraf/video tüm ekranı kaplar,
# üstte küçük logo + kampanya şeridi, altta kısa bir bantta başlık, fiyat,
# tek satır hizmet bilgisi ve WhatsApp. Hayvanlar ortada açıkça görünür.
# ---------------------------------------------------------------------------
def _sade_mask(top_end, bot_start, bot_full):
    g = Image.new('L', (1, H))
    for y in range(H):
        a = max(0.0, 1 - y / top_end) * 140
        if y > bot_start:
            a = max(a, min(1.0, (y - bot_start) / (bot_full - bot_start)) ** 1.3 * 238)
        g.putpixel((0, y), int(a))
    return g.resize((W, H))


def _fit(d, text, name, size, maxw, lines=1, minsize=26):
    while size > minsize:
        f = font(name, size)
        ls = wrap(d, text, f, maxw)
        if len(ls) <= lines:
            return f, ls
        size -= 4
    f = font(name, minsize)
    return f, wrap(d, text, f, maxw)


def sade_overlay(headline, v=None, tema=None):
    """Sade şablonun şeffaf yazı katmanı (RGBA)."""
    if tema:
        set_tema(tema)
    kamp = variant(v)
    ov = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    M = 64
    fh, hl = _fit(d, headline, 'Poppins-Bold.ttf', 76, W - 2 * M, lines=2, minsize=56)
    hiz = '  •  '.join(CFG['etiketler'])
    fz, _ = _fit(d, hiz, 'Poppins-Medium.ttf', 32, W - 2 * M, lines=1, minsize=24)
    lh = int(fh.size * 1.16)
    PH = 72 + 34
    hareketli = bool((CFG.get('hareketli_etiketler') or {}).get('aktif'))
    bh = 64 + len(hl) * lh + 22 + PH + (30 if hareketli else 26 + fz.size + 30) + 56 + 76
    y0 = H - bh
    ov.paste(Image.new('RGBA', (W, H), GREEN + (255,)), (0, 0), _sade_mask(330, y0 - 210, y0 + 80))
    d = ImageDraw.Draw(ov)

    # logo (sol üst) + kampanya şeridi
    L, lx, ly = 130, M, 120
    lg = Image.open(LOGO).convert('RGB').resize((L, L), Image.LANCZOS)
    m = Image.new('L', (L * 4, L * 4), 0)
    ImageDraw.Draw(m).ellipse((0, 0, L * 4, L * 4), fill=255)
    m = m.resize((L, L), Image.LANCZOS)
    d.ellipse((lx - 6, ly - 6, lx + L + 6, ly + L + 6), fill=CREAM + (255,))
    ov.paste(lg, (lx, ly), m)
    if kamp.get('serit'):
        sx = lx + L + 28
        fs, _ = _fit(d, kamp['serit'], 'Poppins-Bold.ttf', 32, W - sx - M - 52, lines=1, minsize=22)
        tw = d.textlength(kamp['serit'], font=fs)
        sh = fs.size + 32
        sy = ly + (L - sh) // 2
        d.rounded_rectangle((sx, sy, sx + tw + 52, sy + sh), radius=sh // 2, fill=RED + (255,),
                            outline=GOLD + (255,), width=3)
        d.text((sx + 26, sy + sh / 2 + 2), kamp['serit'], font=fs, fill=(255, 255, 255, 255), anchor='lm')

    # alt bant
    y = y0 + 64
    for line in hl:
        d.text((M, y), line, font=fh, fill=CREAM + (255,))
        y += lh
    y += 22
    fo, fn = font('Poppins-Medium.ttf', 34), font('Poppins-Bold.ttf', 72)
    old, new = CFG['eski_fiyat'], CFG['yeni_fiyat']
    wo, wn = d.textlength(old, font=fo), d.textlength(new, font=fn)
    pw = 30 + wo + 20 + wn + 30
    d.rounded_rectangle((M, y, M + pw, y + PH), radius=PH // 2, fill=GOLD + (255,))
    cy = y + PH / 2
    d.text((M + 30, cy), old, font=fo, fill=(92, 74, 40, 255), anchor='lm')
    d.line((M + 26, cy + 2, M + 34 + wo, cy + 2), fill=(170, 20, 30, 255), width=5)
    d.text((M + 30 + wo + 20, cy + 4), new, font=fn, fill=GREEN + (255,), anchor='lm')
    suf = CFG['fiyat_ek'].strip()
    a, b = suf.rsplit(' ', 1) if ' ' in suf else (suf, '')
    fs2 = font('Poppins-Medium.ttf', 32)
    d.text((M + pw + 18, cy - 20), a, font=fs2, fill=CREAM + (255,), anchor='lm')
    d.text((M + pw + 18, cy + 20), b, font=fs2, fill=CREAM + (255,), anchor='lm')
    if hareketli:
        y += PH + 30
    else:
        y += PH + 26
        d.text((M, y), hiz, font=fz, fill=(232, 236, 228, 255))
        y += fz.size + 30
    r = 28
    cx, cyy = M + r, y + r
    d.ellipse((cx - r, cyy - r, cx + r, cyy + r), fill=(37, 211, 102, 255))
    d.text((cx, cyy), 'WA', font=font('Poppins-Bold.ttf', 22), fill=(255, 255, 255, 255), anchor='mm')
    d.text((M + 2 * r + 16, cyy + 2), 'WhatsApp  ' + CFG['whatsapp'], font=font('Poppins-Bold.ttf', 46),
           fill=CREAM + (255,), anchor='lm')
    return ov


def sade_aktif():
    return CFG.get('sablon', 'sade') == 'sade'


def foto_story_video(photo, headline, out, ybias=0.5, xbias=0.5, tema=None, v=None):
    """Fotoğraflı story'yi hareketli etiketli 10 sn videoya çevirir (sade şablon)."""
    import hareket
    set_tema(tema)
    src = ImageOps.exif_transpose(Image.open(photo))
    kr = CFG.get('kirpma', {}).get(os.path.basename(photo))
    base = cover(src, int(W * 1.0), H, ybias if kr else 0.5, xbias)
    hareket.foto_video(base, sade_overlay(headline, v, tema), out)


def make(photo, label, headline, body, out, ybias=0.35, xbias=0.5, tema=None, v=None, wybias=0.55, yerlesim=None):
    mod = yerlesim or CFG.get('yerlesim', 'pencere')
    if sade_aktif() and yerlesim != 'tam':
        set_tema(tema)
        src0 = photo if isinstance(photo, Image.Image) else Image.open(photo)
        src0 = ImageOps.exif_transpose(src0) if not isinstance(photo, Image.Image) else src0
        base = cover(src0, W, H, ybias if CFG.get('kirpma', {}).get(os.path.basename(str(photo))) else 0.5, xbias)
        base = Image.alpha_composite(base.convert('RGBA'), sade_overlay(headline, v, tema)).convert('RGB')
        if out is None:
            return base
        base.save(out, quality=92)
        return
    set_tema(tema)
    kamp = variant(v)
    src = photo if isinstance(photo, Image.Image) else Image.open(photo)
    d = ImageDraw.Draw(Image.new('RGB', (W, H)))  # yalnızca ölçü için
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

    if mod == 'pencere':
        # Fotoğraf yazının üstünde kalan alana sığdırılır; alttaki hayvanlar görünsün diye
        # fotoğrafın alt-orta kısmı seçilir (kirpma'daki ybias ile ayarlanabilir).
        hw = min(H, y + 140)
        win = cover(src, W, hw, wybias, xbias)
        base = Image.new('RGB', (W, H), GREEN)
        base.paste(win, (0, 0))
        f0, f1 = y - 260, y + 40
    else:
        base = cover(src, W, H, ybias, xbias)
        f0, f1 = H * (0.20 if kamp else 0.28), H * (0.20 if kamp else 0.28) + H * 0.24
    grad = Image.new('L', (1, H))
    for yy in range(H):
        top = max(0, 1 - yy / 520) * 170
        bot = 0 if yy < f0 else min(1, (yy - f0) / (f1 - f0)) ** 1.2 * 248
        if yy >= f1:
            bot = 255 if mod == 'pencere' else bot
        grad.putpixel((0, yy), int(max(top, bot)))
    grad = grad.resize((W, H))
    base = Image.composite(Image.new('RGB', (W, H), GREEN), base, grad)
    base, ly = logo_disc(base, 170 if kamp else 230, 175)
    d = ImageDraw.Draw(base)
    if kamp.get('serit'):
        ribbon(d, ly + 22, kamp['serit'])

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

    if out is None:
        return base
    base.save(out, quality=92)


def overlay_png(label, headline, out, tema=None, v=None):
    """Story yazı katmanını şeffaf PNG olarak üretir (videonun üstüne bindirmek için).
    Siyah ve beyaz zemin üzerinde iki kez çizip farkından saydamlığı hesaplar."""
    if sade_aktif():
        sade_overlay(headline, v, tema).save(out)
        return
    import numpy as np
    a = np.asarray(make(Image.new('RGB', (W, H), (0, 0, 0)), label, headline, '', None, tema=tema, v=v, yerlesim='tam'),
                   dtype=np.float32)
    b = np.asarray(make(Image.new('RGB', (W, H), (255, 255, 255)), label, headline, '', None, tema=tema, v=v, yerlesim='tam'),
                   dtype=np.float32)
    alpha = 1.0 - (b - a).mean(axis=2) / 255.0
    alpha = np.clip(alpha, 0, 1)
    rgb = np.where(alpha[..., None] > 0.003, a / np.maximum(alpha[..., None], 0.003), 0)
    rgba = np.dstack([np.clip(rgb, 0, 255), alpha * 255]).astype(np.uint8)
    Image.fromarray(rgba, 'RGBA').save(out)


def video_story(video, label, headline, out, tema=None, v=None, sure=10):
    """Videonun üstüne story yazı katmanını bindirir, telifsiz müzik ekler."""
    import subprocess
    import muzik
    png = out[:-4] + '_kat.png'
    wav = out[:-4] + '_muzik.wav'
    overlay_png(label, headline, png, tema=tema, v=v)
    muzik.make(wav, sure, varyant=os.path.basename(out))
    # kısa videolar başa sararak süreyi doldurur
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-stream_loop', '-1', '-i', video, '-i', png, '-i', wav,
                    '-filter_complex',
                    f'[0:v]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},fps=30,trim=duration={sure},'
                    f'setpts=PTS-STARTPTS[v];[v][1:v]overlay=0:0,format=yuv420p[o]',
                    '-map', '[o]', '-map', '2:a', '-t', str(sure), '-c:v', 'libx264', '-preset', 'veryfast',
                    '-crf', '23', '-c:a', 'aac', '-b:a', '128k', '-movflags', '+faststart', out], check=True)
    os.remove(png)
    os.remove(wav)
    import hareket
    if sade_aktif() and hareket.ayar():
        hareket.videoya_ekle(out)


if __name__ == '__main__':
    make(*sys.argv[1:6], ybias=float(sys.argv[6]) if len(sys.argv) > 6 else 0.35)
