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


def videos():
    d = os.path.join(ROOT, 'videolar')
    if not os.path.isdir(d):
        return []
    return sorted(f for f in os.listdir(d) if f.lower().endswith('.mp4'))


def photos():
    d = os.path.join(ROOT, 'fotograflar')
    return sorted(f for f in os.listdir(d) if f.lower().endswith(('.jpg', '.jpeg', '.png')))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('pazartesi', help='haftanın ilk günü (YYYY-MM-DD); 7 gün üretilir')
    ap.add_argument('--gun', help='yalnızca bu tarih (YYYY-MM-DD)')
    ap.add_argument('--sadece', help='yalnızca bu slot adı (sabah/aksam/reels)')
    ap.add_argument('--saat', help='yalnızca bu saat (HH:MM)')
    a = ap.parse_args()

    cfg = story.CFG
    # Hafta, verilen başlangıç gününden itibaren 7 gündür (ör. Cumartesi'den Cuma'ya).
    monday = dt.date.fromisoformat(a.pazartesi)
    week = (monday - EPOCH).days // 7
    ph = photos()
    vids = videos()
    vcount = week * 41
    crop = cfg['kirpma']
    os.makedirs(os.path.join(ROOT, 'stories'), exist_ok=True)
    os.makedirs(os.path.join(ROOT, 'reels'), exist_ok=True)

    # Haftadaki tüm slotlar, sabit sırada (fotoğraf sırası buna göre döner)
    slots = []
    for i in range(7):
        gun = GUNLER[(monday + dt.timedelta(days=i)).weekday()]
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

    # Reels sırası: güne bağlı Reels (ör. "gun": "Cuma") yalnızca o günün ilk Reels'inde çıkar.
    # O slotun normal sırası, güne bağlı Reels'e denk gelen slota verilir (haftada tekrar olmaz).
    reels_pool = cfg['reels']
    reel_idx = {}
    rc = {}
    haftalik_reels = sum(1 for _, _, s in slots if s['tur'] != 'story') or 1
    for k, (i, gun, s) in enumerate(slots):
        if s['tur'] != 'story':
            n = rc.get(s['ad'], 0)
            rc[s['ad']] = n + 1
            reel_idx[k] = (n, (week * haftalik_reels + n) % len(reels_pool))
    for bi, bspec in enumerate(reels_pool):
        bgun = bspec.get('gun')
        if not bgun:
            continue
        hedef = next((k for k, (i, gun, s) in enumerate(slots) if k in reel_idx and gun == bgun), None)
        for k in reel_idx:
            if k != hedef and reel_idx[k][1] == bi:
                reel_idx[k] = (reel_idx[k][0], reel_idx[hedef][1] if hedef is not None else (bi + 1) % len(reels_pool))
        if hedef is not None:
            reel_idx[hedef] = (reel_idx[hedef][0], bi)

    for k, (i, gun, s) in enumerate(slots):
        day = monday + dt.timedelta(days=i)
        need = 4 if s['tur'] == 'reels' else 1
        my_photos = [ph[(pcount + j) % len(ph)] for j in range(need + 1)]
        pcount += need + 1
        # videolu mu? Reels her zaman (video varsa); story'lerin yaklaşık üçte biri
        use_video = bool(vids) and (s['tur'] == 'reels' or k % 2 == 1)
        my_vids = []
        if use_video:
            nv = 3 if s['tur'] == 'reels' else 1
            my_vids = [vids[(vcount + j) % len(vids)] for j in range(nv)]
            vcount += nv
        if a.gun and day.isoformat() != a.gun:
            continue
        if a.sadece and s['ad'] != a.sadece:
            continue
        if a.saat and s['saat'] != a.saat:
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
            if my_vids:
                out = os.path.join('stories', stamp + '.mp4')
                story.video_story(os.path.join(ROOT, 'videolar', my_vids[0]), lab, head, os.path.join(ROOT, out),
                                  tema=tema, v=week * 211 + k)
            else:
                p = my_photos[0]
                kr = crop.get(p, [0.5, 0.35])
                xb, yb = kr[0], kr[1]
                wyb = kr[2] if len(kr) > 2 else 0.55   # 3. değer: fotoğraf penceresinin dikey konumu (0 üst, 1 alt)
                import hareket
                if story.sade_aktif() and hareket.ayar() and hareket.ayar().get('fotograf_story_video'):
                    out = os.path.join('stories', stamp + '.mp4')
                    story.foto_story_video(os.path.join(ROOT, 'fotograflar', p), head, os.path.join(ROOT, out),
                                           ybias=yb, xbias=xb, tema=tema, v=week * 211 + k)
                else:
                    out = os.path.join('stories', stamp + '.jpg')
                    story.make(os.path.join(ROOT, 'fotograflar', p), lab, head, body, os.path.join(ROOT, out),
                               ybias=yb, xbias=xb, tema=tema, v=week * 211 + k, wybias=wyb)
            plan.append({'tarih': tarih, 'tur': 'STORY', 'baslik': head, 'url': RAW + out})
        else:
            n, ridx = reel_idx[k]
            spec = reels_pool[ridx]
            sl = spec['slaytlar']
            src = my_vids if my_vids else my_photos[:need]
            js = {'slaytlar': [[src[j % len(src)], t, h] for j, (t, h) in enumerate(sl)],
                  'kapanis': [my_photos[need]] + spec['kapanis'], 'tema': tema, 'v': week * 211 + k,
                  'video': bool(my_vids)}
            json.dump(js, open(os.path.join(ROOT, 'reels', stamp + '.json'), 'w', encoding='utf-8'),
                      ensure_ascii=False, indent=1)
            reel.build(stamp)
            muz = cfg['reels_muzik'][(week + n) % len(cfg['reels_muzik'])]
            kp = cfg.get('kampanya') or {}
            v = week * 211 + k
            ekler = kp.get('aciklama_ekleri') or [kp.get('aciklama_ek', '')]
            son = kp.get('aciklama_son') or ['']
            acik = ekler[v % len(ekler)] + spec['aciklama']
            if '0533' not in spec['aciklama']:
                acik += '\n\n' + son[v % len(son)]
            item = {'tarih': tarih, 'tur': 'REEL', 'baslik': sl[0][1],
                    'url': RAW + 'reels/' + stamp + '.mp4', 'aciklama': acik, 'muzik': muz}
            rk = cfg.get('reklam') or {}
            if rk.get('aktif') and gun in rk.get('gunler', []) and s['saat'] == rk.get('saat'):
                item['reklam_butce'] = rk['butce_tl']
                item['reklam_odeyen'] = rk['odeyen']
            plan.append(item)
    print(json.dumps(plan, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
