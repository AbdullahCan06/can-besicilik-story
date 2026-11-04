"""Hareketli (pop-up / büyüyüp küçülen) etiketler.

ayarlar.json:
  "hareketli_etiketler": {"aktif": true, "metinler": ["KREDİ KARTI GEÇERLİ • KOMİSYONSUZ", ...]}

Etiketler sırayla, aynı yerde belirir: önce "pop" diye büyüyerek gelir, ekranda
kaldığı sürece hafifçe büyüyüp küçülür (nabız), sonra küçülerek kaybolur.
"""
import os
import subprocess

from PIL import Image, ImageDraw

import story

W, H, FPS = 1080, 1920, 30
Y_MERKEZ = 430          # etiketin dikey merkezi (logonun altı, genelde çadır tavanı hizası)


def ayar():
    a = story.CFG.get('hareketli_etiketler') or {}
    return a if a.get('aktif') and a.get('metinler') else None


def etiket_png(text, out, i=0):
    """Altın çerçeveli, onay işaretli büyük etiket (şeffaf PNG)."""
    f = story.font('Poppins-Bold.ttf', 52)
    tmp = ImageDraw.Draw(Image.new('RGB', (10, 10)))
    tw = tmp.textlength(text, font=f)
    while tw > W - 220 and f.size > 34:
        f = story.font('Poppins-Bold.ttf', f.size - 4)
        tw = tmp.textlength(text, font=f)
    h = f.size + 50
    r = h // 2 - 12
    w = int(30 + 2 * r + 18 + tw + 40)
    pad = 24                                  # gölge payı
    im = Image.new('RGBA', (w + 2 * pad, h + 2 * pad), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((pad + 4, pad + 10, pad + w + 4, pad + h + 10), radius=h // 2, fill=(0, 0, 0, 90))
    fill = story.RED if i % 2 == 0 else story.GREEN
    d.rounded_rectangle((pad, pad, pad + w, pad + h), radius=h // 2, fill=fill + (255,),
                        outline=story.GOLD + (255,), width=5)
    cx, cy = pad + 30 + r, pad + h / 2
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=story.GOLD + (255,))
    k = r / 22
    d.line([(cx - 10 * k, cy), (cx - 3 * k, cy + 8 * k), (cx + 11 * k, cy - 8 * k)], fill=fill + (255,),
           width=max(4, int(6 * k)), joint='curve')
    d.text((pad + 30 + 2 * r + 18, cy + 2), text, font=f, fill=(255, 255, 255, 255), anchor='lm')
    im.save(out)


def _olcek(a, T):
    """t anındaki ölçek (a: etiketin başladığı saniye, T: ekranda kalma süresi)."""
    tl = f'(t-{a:.3f})'
    return (f"if(lt({tl},0.22),0.05+1.15*{tl}/0.22,"
            f"if(lt({tl},0.36),1.2-0.2*({tl}-0.22)/0.14,"
            f"if(gt({tl},{T - 0.2:.3f}),max(0.05,({T:.3f}-{tl})/0.2),"
            f"1+0.07*sin(2*PI*1.6*({tl}-0.36)))))")


def filtre(base_label, ilk_giris, n, sure, out_label='o'):
    """[base_label] videosuna, ilk_giris numaralı girişten başlayan n etiket PNG'sini sırayla bindirir."""
    T = sure / n
    parts, cur = [], base_label
    for i in range(n):
        a, b = i * T, (i + 1) * T
        s = _olcek(a, T)
        parts.append(f"[{ilk_giris + i}:v]format=rgba,scale=w='max(2,iw*{s})':h='max(2,ih*{s})':eval=frame[e{i}]")
        nxt = out_label if i == n - 1 else f'b{i}'
        parts.append(f"[{cur}][e{i}]overlay=x='(W-w)/2':y='{Y_MERKEZ}-h/2':eval=frame:"
                     f"enable='between(t,{a:.3f},{b - 0.01:.3f})'[{nxt}]")
        cur = nxt
    return ';'.join(parts)


def etiket_girisleri(tmpdir, sure):
    """ffmpeg giriş argümanları ve etiket sayısı."""
    a = ayar()
    args = []
    for i, t in enumerate(a['metinler']):
        p = os.path.join(tmpdir, f'etiket{i}.png')
        etiket_png(t, p, i)
        args += ['-loop', '1', '-framerate', str(FPS), '-t', f'{sure}', '-i', p]
    return args, len(a['metinler'])


def foto_video(photo_img, overlay_rgba, out, sure=10, varyant=None):
    """Fotoğraflı story'yi hareketli etiketli kısa videoya çevirir (hafif yakınlaşma + müzik)."""
    import muzik
    tmp = out[:-4] + '_tmp'
    os.makedirs(tmp, exist_ok=True)
    bp, op, wav = os.path.join(tmp, 'zemin.jpg'), os.path.join(tmp, 'yazi.png'), os.path.join(tmp, 'm.wav')
    photo_img.convert('RGB').save(bp, quality=94)
    overlay_rgba.save(op)
    muzik.make(wav, sure, varyant=varyant or os.path.basename(out))
    eargs, n = etiket_girisleri(tmp, sure)
    fc = (f"[0:v]scale=w='{W}*(1+0.06*t/{sure})':h=-2:eval=frame,crop={W}:{H},setsar=1[z];"
          f"[z][1:v]overlay=0:0[y];" + filtre('y', 3, n, sure) + ";[o]format=yuv420p[v]")
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-loop', '1', '-framerate', str(FPS), '-t', str(sure),
                    '-i', bp, '-loop', '1', '-framerate', str(FPS), '-t', str(sure), '-i', op, '-i', wav] + eargs +
                   ['-filter_complex', fc, '-map', '[v]', '-map', '2:a', '-t', str(sure),
                    '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '23', '-c:a', 'aac', '-b:a', '128k',
                    '-movflags', '+faststart', out], check=True)
    import shutil
    shutil.rmtree(tmp)
    import reel
    reel.normalize(out)


def videoya_ekle(path):
    """Hazır bir videonun (Reels) üstüne hareketli etiketleri bindirir; ses aynen kalır."""
    sure = float(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
                                          '-of', 'csv=p=0', path]).decode().strip())
    tmp = path[:-4] + '_et'
    os.makedirs(tmp, exist_ok=True)
    eargs, n = etiket_girisleri(tmp, sure)
    out = path[:-4] + '_et.mp4'
    fc = filtre('0:v', 1, n, sure) + ';[o]format=yuv420p[v]'
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', path] + eargs +
                   ['-filter_complex', fc, '-map', '[v]', '-map', '0:a?', '-t', f'{sure}',
                    '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '22', '-c:a', 'copy',
                    '-movflags', '+faststart', out], check=True)
    os.replace(out, path)
    import shutil
    shutil.rmtree(tmp)
