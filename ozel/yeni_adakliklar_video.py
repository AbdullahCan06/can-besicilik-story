"""Özel paylaşım: müşteri videosuna kalp atışlı başlık, fiyat rozeti ve alt bilgi ekler.
Kullanım: python3 ozel/yeni_adakliklar_video.py <girdi.mp4> <cikti.mp4>"""
import sys, os, math, subprocess, numpy as np
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ROOT); os.chdir(ROOT)
from PIL import Image, ImageDraw, ImageFilter
import story, muzik, reel
W, H, FPS = 1080, 1920, 30
SRC, OUT = sys.argv[1], sys.argv[2]
F = story.font
RED, GOLD, GREEN, CREAM = (200, 16, 46), (214, 178, 104), (16, 66, 44), (248, 243, 230)

def heart(d, cx, cy, s, fill):
    r = s * 0.3
    d.ellipse((cx - 2 * r, cy - r * 1.4, cx, cy + r * 0.6), fill=fill)
    d.ellipse((cx, cy - r * 1.4, cx + 2 * r, cy + r * 0.6), fill=fill)
    d.polygon([(cx - 1.95 * r, cy - 0.1 * r), (cx + 1.95 * r, cy - 0.1 * r), (cx, cy + 2.1 * r)], fill=fill)

# 1) Başlık (kalp atışı ile ölçeklenecek)
txt = 'YENİ ADAKLIKLAR GELDİ!'
sz = 78
while True:
    f = F('Poppins-Bold.ttf', sz)
    tw = ImageDraw.Draw(Image.new('RGB', (1, 1))).textlength(txt, font=f)
    if tw + 230 <= 880: break
    sz -= 2
bw, bh = int(tw + 230), int(sz * 1.75)
head = Image.new('RGBA', (bw + 40, bh + 40), (0, 0, 0, 0))
d = ImageDraw.Draw(head)
d.rounded_rectangle((26, 30, bw + 26, bh + 30), radius=bh // 2, fill=(0, 0, 0, 110))
d.rounded_rectangle((20, 20, bw + 20, bh + 20), radius=bh // 2, fill=RED + (255,), outline=GOLD + (255,), width=6)
d.text((20 + bw / 2, 20 + bh / 2 + 2), txt, font=f, fill=(255, 255, 255, 255), anchor='mm')
heart(d, 20 + 55, 20 + bh / 2 - 4, 50, (255, 255, 255, 255))
heart(d, 20 + bw - 55, 20 + bh / 2 - 4, 50, (255, 255, 255, 255))
HEAD_Y = 290  # merkez (Instagram üst çubuğunun altı)

# 2) Sabit katman: fiyat rozeti (sol üst köşe) + alt bilgi paneli
ov = Image.new('RGBA', (W, H), (0, 0, 0, 0))
# alt bilgi için hafif karartma
g = Image.new('L', (1, H), 0)
for y in range(1180, H):
    g.putpixel((0, y), int(min(1, (y - 1180) / 260) * 170))
ov.paste(Image.new('RGBA', (W, H), (0, 0, 0, 255)), (0, 0), g.resize((W, H)))
d = ImageDraw.Draw(ov)
cx, cy, R = 185, 560, 160
sh = Image.new('L', (W, H), 0); ImageDraw.Draw(sh).ellipse((cx - R, cy - R + 12, cx + R, cy + R + 12), fill=120)
ov.paste(Image.new('RGBA', (W, H), (0, 0, 0, 255)), (0, 0), sh.filter(ImageFilter.GaussianBlur(12)))
pts = []
for i in range(48):
    a = math.pi * 2 * i / 48
    rr = R if i % 2 == 0 else R - 12
    pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
d.polygon(pts, fill=GOLD + (255,))
d.ellipse((cx - R + 22, cy - R + 22, cx + R - 22, cy + R - 22), outline=GREEN + (255,), width=4)
d.text((cx, cy - 58), 'Fiyatlarımız', font=F('Poppins-Medium.ttf', 30), fill=GREEN + (255,), anchor='mm')
d.text((cx, cy + 2), story.CFG['yeni_fiyat'], font=F('Poppins-Bold.ttf', 54), fill=GREEN + (255,), anchor='mm')
d.text((cx, cy + 60), "'den başlıyor", font=F('Poppins-Medium.ttf', 30), fill=GREEN + (255,), anchor='mm')
# alt bilgi
X0, X1 = 50, 950
fb = F('Poppins-Bold.ttf', 58)
y = 1330
for line in ['Hafta sonu adaklık kesmek', 'isteyenleri bekleriz']:
    d.text(((X0 + X1) / 2, y), line, font=fb, fill=(255, 255, 255, 255), anchor='mm', stroke_width=3, stroke_fill=(0, 0, 0, 160))
    y += 74
y += 40
fc = F('Poppins-Bold.ttf', 44)
chips = ['Kesim bizden', 'Kredi kartı geçerli']
ws = [d.textlength(c, font=fc) + 110 for c in chips]
x = (X0 + X1) / 2 - (sum(ws) + 24) / 2
ch = 84
for c, w in zip(chips, ws):
    d.rounded_rectangle((x, y - ch / 2, x + w, y + ch / 2), radius=ch // 2, fill=GREEN + (235,), outline=GOLD + (255,), width=4)
    d.ellipse((x + 18, y - 22, x + 62, y + 22), fill=GOLD + (255,))
    d.line([(x + 29, y + 1), (x + 37, y + 10), (x + 52, y - 9)], fill=GREEN + (255,), width=5)
    d.text((x + 76, y + 2), c, font=fc, fill=(255, 255, 255, 255), anchor='lm')
    x += w + 24
ovn = np.asarray(ov).astype(np.float32)
oa = ovn[..., 3:4] / 255.0

def scale_at(t):
    p = t % 1.0
    def bump(c, w, amp): return amp * math.exp(-((p - c) / w) ** 2)
    return 1 + bump(0.10, 0.06, 0.13) + bump(0.32, 0.06, 0.08)

dur = float(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', SRC]).decode())
n = int(dur * FPS)
dec = subprocess.Popen(['ffmpeg', '-loglevel', 'error', '-i', SRC, '-vf',
                        f'scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},fps={FPS}',
                        '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], stdout=subprocess.PIPE)
tmpv = OUT[:-4] + '_v.mp4'
enc = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}',
                        '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '18',
                        '-pix_fmt', 'yuv420p', tmpv], stdin=subprocess.PIPE)
i = 0
while True:
    buf = dec.stdout.read(W * H * 3)
    if len(buf) < W * H * 3: break
    fr = np.frombuffer(buf, np.uint8).reshape(H, W, 3).astype(np.float32)
    fr = fr * (1 - oa) + ovn[..., :3] * oa
    im = Image.fromarray(fr.astype(np.uint8))
    s = scale_at(i / FPS)
    hh = head.resize((int(head.width * s), int(head.height * s)), Image.LANCZOS)
    im.paste(hh, ((W - hh.width) // 2, HEAD_Y - hh.height // 2), hh)
    enc.stdin.write(im.tobytes()); i += 1
enc.stdin.close(); enc.wait(); dec.wait()
wav = OUT[:-4] + '_m.wav'
muzik.make(wav, dur, varyant='yeni-adakliklar')
subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', tmpv, '-i', SRC, '-i', wav, '-filter_complex',
                '[1:a]volume=0.35[a1];[2:a]volume=0.55[a2];[a1][a2]amix=inputs=2:duration=first:normalize=0[a]',
                '-map', '0:v', '-map', '[a]', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '160k', '-shortest', OUT], check=True)
os.remove(tmpv); os.remove(wav)
reel.normalize(OUT)
print('ok', i, 'kare', 'baslik', sz, bw)
