# Can Besicilik – Instagram story otomasyonu

Her hafta Pazartesi, Çarşamba, Cuma ve Pazar günleri saat 17:00'de Instagram story'si paylaşılır.

- `fotograflar/` – story'lerde kullanılan fotoğraflar (sırayla döner)
- `ayarlar.json` – fiyat, WhatsApp numarası, etiketler, günler, saat ve story metinleri
- `stories/` – üretilen story görselleri (Metricool buradaki linklerden çeker)
- `story.py` – tek bir story tasarlar
- `hafta.py` – bir haftanın story'lerini üretir: `python3 hafta.py 2026-11-02`

Fiyat veya numara değişirse yalnızca `ayarlar.json` güncellenir.
