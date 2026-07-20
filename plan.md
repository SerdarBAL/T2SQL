# T2SQL — Günlük Çalışma Planı (Roadmap)

> **Başlangıç:** Pazartesi, 20 Temmuz 2026
> **Tahmini bitiş:** ~13 Ağustos 2026 (~25 gün, dinlenme günleri dahil)
> **Varsayılan tempo:** Günde ~3–5 saat odaklı çalışma. Tempo değişirse takvim kayar, sıralama sabit.
> **İki bitiş hedefi:**
> 1. Proje sonunda **"Bir AI engineer'ın ihtiyaç duyduğu kadar SQL biliyorum"** diyebilmek → her fazda SQL öğrenme durakları (🎓 SQL) var.
> 2. **"Deployment tarafında iyiyim"** diyebilmek → Faz 5 kasıtlı olarak geniş ve derin tutuldu.

---

## Faz Özeti

| Faz | Gün Aralığı | Konu | Çıktı |
|-----|-------------|------|-------|
| **0** | 1–3 | Kurulum + Veri + SQL temelleri | Postgres'te dolu Olist DB |
| **1** | 4–9 | Agent çekirdeği + self-correction | Soru → SQL → doğru sonuç |
| **2** | 10–11 | Görselleştirme + streaming | Grafik/tablo döndüren API (SSE) |
| **3** | 12–16 | Frontend (Next.js) | Çalışan profesyonel chat UI |
| **4** | 17–18 | LSTM öngörü | Gelir tahmini canlı |
| **5** | 19–23 | DevOps / Deployment | Public URL'de canlı + CI/CD |
| **6** | 24–25 | Cila + Portfolyo | Demoya hazır, README + video |

---

## FAZ 0 — Kurulum, Veri ve SQL Temelleri

### Gün 1 — Pzt, 20 Tem
- Repo iskeleti: klasör yapısı (`backend/`, `frontend/`, `models/`, `docs/`, `data/`), `git init`, `.gitignore`, README taslağı.
- Ortam: Python 3.11 venv, Node.js, Docker Desktop çalışıyor mu doğrula.
- Olist datasetini indir (Kaggle: *Brazilian E-Commerce by Olist*), `data/` altına koy.
- 🎓 **SQL:** Veri setini tanı — hangi tablo ne içeriyor, kolonlar, ilişkiler (ER kafanda otursun).

### Gün 2 — Sal, 21 Tem
- `docker-compose.yml`: PostgreSQL 16 servisi ayağa kaldır.
- Olist CSV'lerini Postgres'e yükle (`init.sql` / seed script). psql veya pgAdmin ile bağlan.
- 🎓 **SQL:** `SELECT`, `WHERE`, `ORDER BY`, `LIMIT`, `DISTINCT`. Tabloları elle keşfet. `docs/sql-notes.md` başlat.

### Gün 3 — Çar, 22 Tem
- 🎓 **SQL (önemli gün):** `JOIN` türleri (orders ↔ order_items ↔ products), `GROUP BY`, aggregate (`SUM`, `COUNT`, `AVG`), `HAVING`.
- İlk gerçek analitik sorgu: **kategori bazında toplam gelir**. `date_trunc` ile aylık gelir zaman serisi (LSTM için de lazım olacak).
- Bu sorguları `sql-notes.md`'ye açıklamalarıyla kaydet.

---

## FAZ 1 — Agent Çekirdeği (LangGraph)

### Gün 4 — Per, 23 Tem
- FastAPI iskeleti, `/api/health`. Gemini API bağlantısı (`langchain-google-genai`), `.env` + secret yönetimi.
- Şema introspection fonksiyonu (SQLAlchemy ile tablo/kolon listesi çıkar).
- Basit test: soru → LLM → düz metin cevap.

### Gün 5 — Cum, 24 Tem
- LangGraph `AgentState` + düğümler: `classify_intent`, `fetch_schema`, `generate_sql`, `validate_sql` (yalnızca-SELECT guard, yasaklı kelime filtresi).
- 🎓 **SQL:** Agent'ın ürettiği SQL'leri oku, doğru mu değerlendir — bu senin SQL gözünü geliştirir.

### Gün 6 — Cmt, 25 Tem
- `execute_sql`: read-only DB rolü oluştur, statement timeout (10s), otomatik `LIMIT`.
- Happy-path uçtan uca: soru → SQL → sonuç (henüz hata düzeltme yok).

### Gün 7 — Paz, 26 Tem
- 🛋️ **Buffer / dinlenme.** İstersen: few-shot örneklerle prompt iyileştirme, birikmiş işleri toparlama.

### Gün 8 — Pzt, 27 Tem
- `self_correct` döngüsü: DB hata mesajı → LLM → düzeltilmiş SQL → tekrar `execute_sql` (max 3 deneme) → `graceful_fail`.
- Kasıtlı hata senaryolarıyla test et (yanlış kolon adı, yanlış tablo, tip hatası).

### Gün 9 — Sal, 28 Tem
- `summarize` düğümü: **İngilizce özet** (v1 dil politikası) + SQL açıklaması üretimi.
- `pytest` ile agent unit testleri (birkaç örnek soru → beklenen davranış).
- 🎓 **SQL (ileri):** `WINDOW` fonksiyonları (`LAG`, `OVER`, dönem karşılaştırması) — "Q3'te en yüksek gelir artışı" sorusunun çözümü.

---

## FAZ 2 — Görselleştirme + Streaming

### Gün 10 — Çar, 29 Tem
- `decide_visualization` düğümü: sonucun yapısına göre grafik tipi seçimi (bar / line / pie / table). `viz_spec` üretimi (Plotly uyumlu).

### Gün 11 — Per, 30 Tem
- `/api/chat` **SSE streaming**: `step`, `sql`, `result`, `answer`, `done` eventleri.
- curl / terminalden uçtan uca test — frontend'e hazır API.

---

## FAZ 3 — Frontend (Next.js)

### Gün 12 — Cum, 31 Tem
- Next.js 14 (App Router) + Tailwind + shadcn/ui kurulum.
- Chat UI iskeleti: mesaj balonları, input, gönderme. (Tüm UI metinleri **İngilizce** — v1 politikası.)

### Gün 13 — Cmt, 1 Ağu
- SSE tüketimi: streaming yanıt render, token-token akış.
- Adım göstergesi (stepper): "Generating SQL...", "Running query...", "Self-correcting...".

### Gün 14 — Paz, 2 Ağu
- 🛋️ **Buffer / dinlenme** veya UI ince ayar.

### Gün 15 — Pzt, 3 Ağu
- Dinamik tablo bileşeni (sortable / scrollable) + **Framer Motion** "yükselerek açılma" animasyonu.

### Gün 16 — Sal, 4 Ağu
- Plotly.js grafik paneli (interaktif, tam ekran).
- SQL açıklama paneli (katlanabilir — 🎓 öğrenme hedefi). Light/dark tema.

---

## FAZ 4 — LSTM Öngörü

### Gün 17 — Çar, 5 Ağu
- Offline eğitim (notebook): SQL ile gelir zaman serisi çıkar → normalize (scaler) → LSTM eğit (PyTorch) → `models/`'a model + scaler kaydet.

### Gün 18 — Per, 6 Ağu
- `forecast` düğümü + inference: seriyi çek → tahmin et → denormalize.
- Grafik: geçmiş + tahmin (tahmin kısmı kesikli çizgi). Agent akışına entegre.

---

## FAZ 5 — DevOps / Deployment  ⭐ (güçlenmek istediğin alan)

### Gün 19 — Cum, 7 Ağu
- Backend + frontend için **multi-stage Dockerfile**. `.dockerignore`, image boyutu küçültme.
- `docker-compose` ile tam yığın (backend + frontend + postgres) lokalde tek komutla ayağa kalksın.

### Gün 20 — Cmt, 8 Ağu
- **GitHub Actions CI:** lint (`ruff` + `eslint`), test (`pytest` + frontend build), Docker build.
- Branch protection, PR üzerinde otomatik kontrol.

### Gün 21 — Paz, 9 Ağu
- 🛋️ **Buffer / dinlenme.**

### Gün 22 — Pzt, 10 Ağu
- **Railway deploy:** managed Postgres + backend servisi, env/secrets yönetimi, health check, Olist seed'i prod DB'ye yükleme.

### Gün 23 — Sal, 11 Ağu
- Frontend deploy, CORS ayarı, domain.
- **CD:** `main`'e merge → otomatik deploy. Canlı ortamda smoke test.

---

## FAZ 6 — Cila + Portfolyo

### Gün 24 — Çar, 12 Ağu
- UX cila: loading/empty/error durumları, rate limiting, kenar senaryolar.
- Uçtan uca canlı test (birçok örnek soru).

### Gün 25 — Per, 13 Ağu
- README (mimari diyagram + demo GIF), `sql-notes.md`'yi öğrenilenlerle derle.
- Demo videosu, portfolyo/LinkedIn yazısı.
- 🎓 **SQL kapanış:** Öğrendiğin kalıpları (JOIN, GROUP BY, window fn, CTE, date_trunc) tek dosyada topla → "AI engineer için yeterli SQL" hedefinin kanıtı.

---

## Notlar
- **Kritik yol:** Faz 1 (agent) ve Faz 3 (frontend) en uzun/riskli kısımlar; buralarda takılırsak buffer günleri (7, 14, 21) tamponlar.
- **Paralellik:** Frontend'i (Faz 3) beklerken agent hâlâ iyileştirilebilir; ama tek kişi çalıştığımız için sıralı gidiyoruz.
- **Her fazın sonunda commit + kısa demo** — portfolyoda "incremental progress" güzel görünür.
- Bu plan yaşayan dokümandır; her günün sonunda ✅ işaretleyip ilerlemeyi takip edebiliriz.
