"""Bir haftanın tüm paylaşımlarını (story + Reels) ayarlar.json'daki programa göre üretir.

Kullanım:
  python3 hafta.py 2026-11-02            # o pazartesiden başlayan hafta
  python3 hafta.py 2026-11-02 --gun 2026-11-01 --sadece sabah   # tek gün / tek slot
Çıktı: stories/*.jpg, reels/*.mp4 ve ekrana JSON plan
(tarih, tür, herkese açık link, Reels açıklaması ve müziği).
"""
import argparse
import datetime as dt
import json
import os

import reel
import story

ROOT = os.path.dirname(os.path.abspath(__file__))
RAW = 'https://raw.githubusercontent.com/AbdullahCan06/can-besicilik-story/main/'
GUNLER = ['Pazartesi', 'Salı', 'Çarşamba', 'Perşembe', 'Cuma', 'Cumartesi', 'Pazar']
EPOCH = dt.date(2026, 10, 26)


def photos():
    d = os.path.join(ROOT, 'fotograflar')
    return sorted(f for f in os.listdir(d) if f.lower().endswith(('.jpg', '.jpeg', '.png')))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('pazartesi')
    ap.add_argument('--gun', help='yalnızca bu tarih (YYYY-MM-DD)')
    ap.add_argument('--sadece', help='yalnızca bu slot adı (sabah/aksam/reels)')
    a = ap.parse_args()

    cfg = story.CFG
    monday = dt.date.fromisoformat(a.pazartesi)
    monday -= dt.timedelta(days=monday.weekday())
    if a.gun:
        g = dt.date.fromisoformat(a.gun)
        monday = g - dt.timedelta(days=g.weekday())
    week = (monday - EPOCH).days // 7
    ph = photos()
    crop = cfg['kirpma']
    os.makedirs(os.path.join(ROOT, 'stories'), exist_ok=True)
    os.makedirs(os.path.join(ROOT, 'reels'), exist_ok=True)

    # Haftadaki tüm slotlar, sabit sırada (fotoğraf sırası buna göre döner)
    slots = []
    for i, gun in enumerate(GUNLER):
        for s in cfg['program']:
            if gun in s['gunler']:
                slots.append((i, gun, s))
    slots.sort(key=lambda x: (x[0], x[2]['saat']))

    pcount = week * 37           # haftalık fotoğraf kaydırma
    plan = []
    rcount = {}
    per_day = {}
    for s in cfg['program']:
        per_day[s['ad']] = per_day.get(s['ad'], 0) + 1
    seen = {}
    for k, (i, gun, s) in enumerate(slots):
        day = monday + dt.timedelta(days=i)
        need = 4 if s['tur'] == 'reels' else 1
        my_photos = [ph[(pcount + j) % len(ph)] for j in range(need + 1)]
        pcount += need + 1
        if a.gun and day.isoformat() != a.gun:
            continue
        if a.sadece and s['ad'] != a.sadece:
            continue
        tarih = f"{day.isoformat()}T{s['saat']}:00"
        tema = story.TEMA_SIRASI[(week + k) % len(story.TEMA_SIRASI)]
        stamp = f"{day.isoformat()}-{s['saat'].replace(':', '')}-{s['ad']}"

        if s['tur'] == 'story':
            pool = cfg['sabah_cuma'] if (s['ad'] == 'sabah' and gun == 'Cuma') else cfg[s['ad']]
            key = (i, s['ad'])
            c_i = seen.get(key, 0)
            seen[key] = c_i + 1
            lab, head, body = pool[((week * 7 + i) * per_day[s['ad']] + c_i + week) % len(pool)]
            p = my_photos[0]
            xb, yb = crop.get(p, [0.5, 0.35])
            out = os.path.join('stories', stamp + '.jpg')
            story.make(os.path.join(ROOT, 'fotograflar', p), lab, head, body, os.path.join(ROOT, out),
                       ybias=yb, xbias=xb, tema=tema)
            plan.append({'tarih': tarih, 'tur': 'STORY', 'baslik': head, 'url': RAW + out})
        else:
            n = rcount.get(s['ad'], 0)
            rcount[s['ad']] = n + 1
            spec = cfg['reels'][(week * len(s['gunler']) + n) % len(cfg['reels'])]
            sl = spec['slaytlar']
            js = {'slaytlar': [[my_photos[j % need], t, h] for j, (t, h) in enumerate(sl)],
                  'kapanis': [my_photos[need]] + spec['kapanis'], 'tema': tema}
            json.dump(js, open(os.path.join(ROOT, 'reels', stamp + '.json'), 'w', encoding='utf-8'),
                      ensure_ascii=False, indent=1)
            reel.build(stamp)
            muz = cfg['reels_muzik'][(week + n) % len(cfg['reels_muzik'])]
            plan.append({'tarih': tarih, 'tur': 'REEL', 'baslik': sl[0][1],
                         'url': RAW + 'reels/' + stamp + '.mp4', 'aciklama': (cfg.get('kampanya') or {}).get('aciklama_ek', '') + spec['aciklama'],
                         'muzik': muz})
    print(json.dumps(plan, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
