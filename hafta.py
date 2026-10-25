"""Bir haftanın story'lerini üretir.

Kullanım: python3 hafta.py 2026-10-26   (haftanın pazartesi tarihi)
Çıktı: stories/<tarih>.jpg dosyaları ve ekrana JSON plan
(tarih, saat, görselin herkese açık linki).
Fotoğraf ve metinler hafta numarasına göre sırayla döner, böylece tekrar az olur.
"""
import datetime as dt
import json
import os
import sys

import story

ROOT = os.path.dirname(os.path.abspath(__file__))
RAW = 'https://raw.githubusercontent.com/AbdullahCan06/can-besicilik-story/main/stories/'
OFFSET = {'Pazartesi': 0, 'Salı': 1, 'Çarşamba': 2, 'Perşembe': 3, 'Cuma': 4, 'Cumartesi': 5, 'Pazar': 6}
EPOCH = dt.date(2026, 10, 26)


def main(monday_str):
    cfg = story.CFG
    monday = dt.date.fromisoformat(monday_str)
    monday -= dt.timedelta(days=monday.weekday())
    week = (monday - EPOCH).days // 7

    photos = sorted(f for f in os.listdir(os.path.join(ROOT, 'fotograflar'))
                    if f.lower().endswith(('.jpg', '.jpeg', '.png')))
    os.makedirs(os.path.join(ROOT, 'stories'), exist_ok=True)

    plan = []
    for slot, gun in enumerate(cfg['gunler']):
        day = monday + dt.timedelta(days=OFFSET[gun])
        pool = cfg['metinler'][gun]
        label, head, body = pool[week % len(pool)]
        photo = photos[(week * len(cfg['gunler']) + slot) % len(photos)]
        xbias, ybias = cfg['kirpma'].get(photo, [0.5, 0.35])
        name = f'{day.isoformat()}.jpg'
        story.make(os.path.join(ROOT, 'fotograflar', photo), label, head, body,
                   os.path.join(ROOT, 'stories', name), ybias=ybias, xbias=xbias)
        plan.append({'gun': gun, 'tarih': f"{day.isoformat()}T{cfg['saat']}:00",
                     'foto': photo, 'baslik': head, 'url': RAW + name})
    print(json.dumps(plan, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main(sys.argv[1])
