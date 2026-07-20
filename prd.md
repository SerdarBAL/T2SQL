# PRD — Agentic Text-to-SQL Analitik & Öngörü Platformu

> **Proje kodu:** T2SQL
> **Doküman sürümü:** 1.0
> **Tarih:** 2026-07-20
> **Sahip:** Serdar Bal
> **Durum:** Taslak — geliştirmeye hazır

---

## 1. Özet (Executive Summary)

Kullanıcının doğal dilde sorduğu iş sorularını (ör. *"Hangi ürün kategorisi Q3'te en yüksek gelir artışını gösterdi?"*) **agentic** bir pipeline ile SQL'e çeviren, PostgreSQL üzerinde çalıştıran, hata alırsa veritabanının döndürdüğü hata mesajından **kendini düzelten (self-correcting)**, sonucu hem **doğal dille** hem de **dinamik tablo/grafik** olarak sunan; ayrıca **önceden eğitilmiş bir LSTM modeliyle gelir/satış zaman serisi tahmini** yapan tam yığın (full-stack), containerize edilmiş, CI/CD ile deploy edilen bir web uygulaması.

Veri seti olarak **Brazilian E-Commerce (Olist)** kullanılacaktır.

### Projenin İki Ana Kişisel Hedefi
1. **SQL öğrenmek** — Sistem geliştirilirken agent'ın ürettiği SQL'ler kullanıcıya açıklanacak; bu PRD ve geliştirme sürecinde SQL kavramları öğretici biçimde ele alınacaktır.
2. **Deployment becerisini geliştirmek** — Docker, container orchestration, CI/CD (GitHub Actions) ve bulut deployment (Railway/Render) pratik olarak uygulanacaktır.

---

## 2. Hedefler ve Başarı Kriterleri

### 2.1 Ürün Hedefleri
| # | Hedef | Başarı Kriteri |
|---|-------|----------------|
| G1 | Doğal dil → SQL çevirisi | Örnek soru setinin ≥ %85'i doğru SQL üretip doğru sonuç döndürür |
| G2 | Self-correction | Hatalı SQL üretilirse agent en fazla 3 denemede kendini düzeltir |
| G3 | Görselleştirme | Sonuç tabular olduğunda otomatik olarak uygun grafik/tablo önerilir |
| G4 | LSTM öngörü | Gelir zaman serisi için gelecek N periyot tahmini üretilir ve grafiklenir |
| G5 | Profesyonel UX | Chat generic görünür; tablo/grafik gerektiğinde animasyonla "yükselerek" açılır |
| G6 | Deploy | Uygulama public bir URL'de canlı, CI/CD ile otomatik deploy edilir |

### 2.2 Kişisel/Portfolyo Hedefleri
- Agentic AI (LangGraph state machine, tool-calling, retry döngüleri) yetkinliği göstermek
- SQL analitik sorgu yazma pratiği
- Uçtan uca DevOps (Docker → CI/CD → cloud) deneyimi
- ML entegrasyonu (LSTM inference servisi) gösterimi

### 2.3 Kapsam Dışı (Non-Goals — v1)
- Çoklu kullanıcı auth / rol yönetimi (v1'de tek public demo yeterli, opsiyonel basit gate)
- Gerçek zamanlı veri ingest / streaming
- LSTM'in canlı (online) yeniden eğitimi — model **önceden eğitilir**, sadece inference yapılır
- Birden fazla veri kaynağı (yalnızca Olist Postgres)

---

## 3. Kullanıcı Personası

**Birincil kullanıcı: "Data-savvy profesyonel"**
Bir analist, ürün müdürü veya iş geliştirme uzmanı. SQL bilmeyebilir ama iş sorularını doğal dille ifade edebilir. Hızlı, güvenilir, görsel yanıt bekler. Arayüzün profesyonel ve temiz olmasını önemser.

**İkincil kullanıcı: Portfolyo değerlendiricisi (işveren/teknik mülakatçı)**
Kod kalitesine, mimariye, deployment olgunluğuna bakar.

---

## 4. Örnek Kullanım Senaryoları (User Stories)

1. **Analitik sorgu:** "2017'de en çok gelir getiren 5 ürün kategorisi nedir?" → Agent SQL üretir → çalıştırır → bar chart + tablo + doğal dil özet döner.
2. **Karşılaştırmalı sorgu:** "Q3'te en yüksek gelir artışını hangi kategori gösterdi?" → Agent window function / dönem karşılaştırması içeren SQL üretir.
3. **Self-correction:** Agent yanlış kolon adı kullanır → Postgres `column "x" does not exist` döner → agent hatayı okuyup şemayı yeniden kontrol eder → düzeltilmiş SQL ile tekrar dener.
4. **Öngörü:** "Önümüzdeki 3 ay için toplam gelir tahmini nedir?" → Agent geçmiş gelir zaman serisini SQL ile çeker → LSTM inference servisine gönderir → tahmin grafiği (geçmiş + gelecek) döner.
5. **Takip sorusu:** "Peki bunu sadece 'bed_bath_table' kategorisi için göster" → Agent önceki bağlamı kullanarak sorguyu daraltır.

---

## 5. Sistem Mimarisi

### 5.1 Yüksek Seviye Diyagram

```
┌──────────────────────────────────────────────────────────────┐
│                      FRONTEND (Next.js + React)               │
│  Chat UI  │  Dinamik Tablo Paneli  │  Grafik Paneli (Plotly)  │
└───────────────────────────┬──────────────────────────────────┘
                            │ REST / SSE (streaming)
┌───────────────────────────▼──────────────────────────────────┐
│                    BACKEND API (FastAPI)                       │
│  ┌────────────────────────────────────────────────────────┐  │
│  │              LANGGRAPH AGENT (state machine)            │  │
│  │  intent → schema-fetch → generate-SQL → validate →     │  │
│  │  execute → (error? → self-correct loop) → summarize →  │  │
│  │  visualize-decision → (forecast? → LSTM node)          │  │
│  └────────────────────────────────────────────────────────┘  │
│      │ LLM: Gemini API        │ Tools: sql_exec, schema,      │
│      │ (provider-agnostic)    │        plot_spec, forecast    │
└──────┼─────────────────────────┼──────────────────────────────┘
       │                         │
┌──────▼──────────┐   ┌──────────▼───────────┐   ┌──────────────┐
│  PostgreSQL      │   │  LSTM Inference       │   │  Gemini API  │
│  (Olist dataset) │   │  (PyTorch/Keras,      │   │  (LLM)       │
│                  │   │   pretrained .pt/.h5) │   │              │
└──────────────────┘   └───────────────────────┘   └──────────────┘
```

### 5.2 Bileşenler

| Katman | Teknoloji | Görev |
|--------|-----------|-------|
| Frontend | **Next.js 14 (App Router) + React + TypeScript** | Chat arayüzü, dinamik tablo/grafik paneli, streaming yanıt |
| UI Kit | **Tailwind CSS + shadcn/ui + Framer Motion** | Profesyonel, temiz tasarım; tablo/grafik "yükselerek açılma" animasyonu |
| Grafik | **Plotly.js** (frontend) / **Plotly** (backend spec üretimi) | İnteraktif grafikler |
| Backend | **FastAPI (Python 3.11+)** | API, agent orchestration, SSE streaming |
| Agent | **LangGraph + LangChain** | State machine, tool-calling, self-correction döngüsü |
| LLM | **Gemini API** (`langchain-google-genai`) | NL→SQL, özetleme, görselleştirme kararı. Provider-agnostic katman |
| Veritabanı | **PostgreSQL 16** | Olist verisi |
| DB erişim | **SQLAlchemy + psycopg** | Şema introspection, güvenli sorgu çalıştırma |
| ML | **PyTorch (veya TensorFlow/Keras)** | Önceden eğitilmiş LSTM inference |
| Container | **Docker + Docker Compose** | Tüm servisleri paketleme |
| CI/CD | **GitHub Actions** | Lint, test, build, deploy |
| Hosting | **Railway** (veya Render) | Container + managed Postgres |

---

## 6. Agent Tasarımı (LangGraph)

### 6.1 State (durum) Şeması
```python
class AgentState(TypedDict):
    question: str                 # kullanıcının sorusu
    chat_history: list            # önceki mesajlar (bağlam)
    db_schema: str                # ilgili tabloların şeması
    generated_sql: str            # üretilen SQL
    sql_result: list | None       # sorgu sonucu
    error: str | None             # DB hata mesajı
    retry_count: int              # kaç kez düzeltme denendi
    needs_forecast: bool          # LSTM gerekli mi
    forecast_result: dict | None  # tahmin çıktısı
    viz_spec: dict | None         # grafik/tablo spesifikasyonu
    final_answer: str             # doğal dil yanıt
```

### 6.2 Düğümler (Nodes) ve Akış

1. **`classify_intent`** — Soru bir veri sorgusu mu, forecast isteği mi, yoksa selamlama/açıklama mı? Yönlendirme yapar.
2. **`fetch_schema`** — İlgili tabloların şemasını (kolon adları, tipleri, örnek değerler) getirir. LLM'e verilir.
3. **`generate_sql`** — LLM şemayı ve soruyu kullanarak SQL üretir. Yalnızca `SELECT` üretmesi zorunlu kılınır (güvenlik).
4. **`validate_sql`** — Statik kontrol: sadece SELECT mi? Yasaklı kelimeler (`DROP`, `DELETE`, `UPDATE`, `INSERT`, `ALTER`) var mı?
5. **`execute_sql`** — Sorguyu Postgres'te çalıştırır.
   - **Başarılı** → `summarize`'a git
   - **Hata** → `self_correct`'e git (retry_count < 3 ise)
6. **`self_correct`** — DB hata mesajını + orijinal SQL'i + şemayı LLM'e verir, düzeltilmiş SQL ister → tekrar `execute_sql`. 3 denemeden sonra vazgeçip kullanıcıya nazik hata mesajı döner.
7. **`decide_forecast`** — Soru gelecek tahmini istiyorsa `forecast` düğümüne yönlendirir.
8. **`forecast`** — Zaman serisi verisini LSTM inference servisine gönderir, tahmini alır.
9. **`decide_visualization`** — Sonuç yapısına göre uygun grafik tipini seçer (bar, line, tablo). `viz_spec` üretir.
10. **`summarize`** — Sonucu doğal dille özetler. **v1 (ilk sürüm) için özet çıktısı İngilizce üretilir** (bkz. Bölüm 9.3 Dil Politikası), SQL'i de açıklamalı olarak ekler (öğretici hedef).

### 6.3 Self-Correction Döngüsü (kritik özellik)
```
generate_sql → validate_sql → execute_sql
                                   │
                          ┌────────┴────────┐
                       success            error
                          │                 │
                     summarize        self_correct ──(retry<3)──► execute_sql
                                              │
                                         (retry=3) → graceful_fail
```

---

## 7. Veri Modeli (Olist Dataset)

Olist ~100k sipariş içeren gerçek bir Brezilya e-ticaret veri setidir. Ana tablolar:

| Tablo | Açıklama | Önemli kolonlar |
|-------|----------|-----------------|
| `olist_orders` | Siparişler | order_id, customer_id, order_status, order_purchase_timestamp |
| `olist_order_items` | Sipariş kalemleri | order_id, product_id, seller_id, price, freight_value |
| `olist_products` | Ürünler | product_id, product_category_name |
| `olist_customers` | Müşteriler | customer_id, customer_state, customer_city |
| `olist_sellers` | Satıcılar | seller_id, seller_state |
| `olist_order_payments` | Ödemeler | order_id, payment_type, payment_value |
| `olist_order_reviews` | Yorumlar | order_id, review_score |
| `product_category_name_translation` | Kategori çevirisi | product_category_name → İngilizce |

**Gelir hesabı için not (SQL öğrenme):** Gelir genelde `olist_order_items.price` toplanarak (opsiyonel `freight_value` dahil) hesaplanır; zaman boyutu `olist_orders.order_purchase_timestamp`'ten gelir. Bu ikisini `order_id` üzerinden `JOIN` etmek gerekir — agent'ın öğreneceği ilk kalıp budur.

---

## 8. LSTM Öngörü Modülü

### 8.1 Kapsam
**Gelir/satış zaman serisi tahmini.** Geçmiş dönemsel (günlük veya aylık) gelir verisi girdi; gelecek N periyodun gelir tahmini çıktı.

### 8.2 Yaklaşım
- **Eğitim (offline, tek seferlik):** Olist'ten aylık/günlük toplam gelir zaman serisi çıkarılır, LSTM eğitilir, model artefaktı (`.pt` veya `.h5`) + scaler (`.pkl`) kaydedilir.
- **Inference (runtime):** Agent forecast istediğinde, ilgili zaman serisini SQL ile çeker → normalize eder → pretrained modele verir → tahmini denormalize edip döndürür.
- Model artefaktı repoda `models/` altında veya bir object storage'da tutulur; container image'a dahil edilir.

### 8.3 Çıktı
- Geçmiş veri + tahmin edilen gelecek değerler tek grafikte (line chart, tahmin kısmı kesikli çizgi).
- Kullanıcıya doğal dil özet (v1'de İngilizce): "Based on the model, revenue is trending up ~X% over the next 3 months."

> **Not (dürüstlük):** LSTM'in Olist gibi ~2 yıllık, kısıtlı ve mevsimsel bir seride tahmin gücü sınırlıdır. Portfolyoda bu bir **pipeline/entegrasyon gösterimi** olarak konumlandırılacak, "kusursuz tahmin" iddiası taşımayacak.

---

## 9. Frontend / UX Gereksinimleri

### 9.1 Tasarım Prensipleri
- **Generic ve temiz chat arayüzü** — varsayılan görünüm ChatGPT benzeri sade bir sohbet.
- **Bağlama duyarlı paneller** — tablo veya grafik gerektiğinde, mesaj balonunun altından/yanından **animasyonla (Framer Motion) yükselerek** bir görselleştirme paneli açılır.
- **Profesyonel görünüm** — nötr renk paleti, iyi tipografi, açık/koyu tema.
- **Streaming** — yanıtlar token-token akar (SSE); agent'ın hangi adımda olduğu kullanıcıya gösterilir. **v1 için tüm UI metinleri İngilizce** (ör. "Generating SQL...", "Running query...", "Self-correcting...").

### 9.3 Dil Politikası (ilk sürüm)
- **UI metinleri (butonlar, etiketler, adım göstergesi, boş durumlar, hata mesajları): İngilizce.**
- **Agent özet (summary) yanıtı: İngilizce.** Kullanıcı Türkçe soru sorsa bile agent yanıtı ve özeti İngilizce döner.
- SQL açıklama paneli metni de İngilizce.
- İleride (v2) çok dilli (TR/EN) destek eklenebilir; bu v1 kapsamı dışındadır.

### 9.2 Ana Bileşenler
| Bileşen | İşlev |
|---------|-------|
| Chat penceresi | Mesaj geçmişi, input, streaming yanıt |
| Adım göstergesi (stepper) | Agent'ın canlı durumu (intent → SQL → execute → viz) |
| Dinamik tablo | Sonuç tabular ise sortable/scrollable tablo, animasyonlu açılış |
| Grafik paneli | Plotly interaktif grafik (bar/line/pie), tam ekran seçeneği |
| SQL görüntüleyici | Üretilen SQL'i açıklamasıyla gösteren katlanabilir panel (**öğrenme hedefi**) |

---

## 10. Backend API Sözleşmesi (taslak)

| Endpoint | Method | Açıklama |
|----------|--------|----------|
| `/api/chat` | POST (SSE) | Soru gönderir, agent adımlarını + final yanıtı streamler |
| `/api/schema` | GET | Veritabanı şemasını döner (debug/UI için) |
| `/api/health` | GET | Health check (deploy için) |
| `/api/forecast` | POST | (opsiyonel ayrık) zaman serisi → tahmin |

**Örnek `/api/chat` yanıt olayları (SSE):**
```
event: step    data: {"node":"generate_sql","status":"running"}
event: sql     data: {"sql":"SELECT ...","explanation":"..."}
event: result  data: {"rows":[...],"viz_spec":{...}}
event: answer  data: {"text":"...token..."}
event: done    data: {}
```

---

## 11. Güvenlik

- **Yalnızca SELECT:** Agent'ın ürettiği SQL statik olarak doğrulanır; `INSERT/UPDATE/DELETE/DROP/ALTER/TRUNCATE/GRANT` içeren sorgular reddedilir.
- **Read-only DB kullanıcısı:** Uygulama Postgres'e yalnızca okuma yetkisi olan bir rol ile bağlanır (savunma katmanı 2).
- **Sorgu limiti:** Otomatik `LIMIT` enjeksiyonu ve statement timeout (ör. 10s) ile pahalı sorgular engellenir.
- **Rate limiting:** Public demo için basit istek sınırı.
- **Secret yönetimi:** API anahtarları (Gemini) yalnızca `.env` / Railway secrets'ta; repoda asla değil.
- **Prompt injection farkındalığı:** Kullanıcı girdisi şema ve sistem promptundan ayrıştırılır.

---

## 12. DevOps / Deployment

### 12.1 Containerization
- `Dockerfile` (backend), `Dockerfile` (frontend), `docker-compose.yml` (lokal: backend + frontend + postgres).
- Postgres seed: Olist CSV'lerini yükleyen `init.sql` / seed script.

### 12.2 CI/CD (GitHub Actions)
| Aşama | İş |
|-------|-----|
| Lint | `ruff` (Python), `eslint` (TS) |
| Test | `pytest` (backend, agent unit testleri), frontend build kontrolü |
| Build | Docker image build |
| Deploy | `main`'e merge'de Railway/Render'a otomatik deploy |

### 12.3 Ortamlar
- **Local:** Docker Compose ile tam yığın.
- **Production:** Railway — backend servisi + frontend servisi + managed PostgreSQL.

---

## 13. Teknoloji Yığını Özeti

```
Frontend : Next.js 14, React, TypeScript, Tailwind, shadcn/ui, Framer Motion, Plotly.js
Backend  : FastAPI, LangGraph, LangChain, langchain-google-genai, SQLAlchemy, psycopg
LLM      : Gemini API (provider-agnostic katman)
Database : PostgreSQL 16 (Olist)
ML       : PyTorch (pretrained LSTM), pandas, scikit-learn (scaler)
DevOps   : Docker, Docker Compose, GitHub Actions, Railway
```

---

## 14. Yol Haritası (Milestones)

| Faz | İçerik | Çıktı |
|-----|--------|-------|
| **M0 — Kurulum** | Repo, Docker Compose, Postgres + Olist seed | Lokalde çalışan boş iskelet + dolu DB |
| **M1 — Agent çekirdeği** | LangGraph: NL→SQL→execute→summarize (self-correction dahil) | Terminal/API'den soru sorup doğru sonuç alma |
| **M2 — Görselleştirme** | viz_spec üretimi + Plotly entegrasyonu | Grafik/tablo döndüren API |
| **M3 — Frontend** | Next.js chat UI, streaming, dinamik tablo/grafik paneli | Çalışan web arayüzü |
| **M4 — LSTM** | Offline eğitim + inference düğümü + forecast grafiği | Tahmin özelliği canlı |
| **M5 — DevOps** | CI/CD pipeline + Railway deploy | Public URL'de canlı uygulama |
| **M6 — Cila** | UX iyileştirme, SQL açıklama paneli, README, demo videosu | Portfolyoya hazır |

---

## 15. Riskler ve Açık Sorular

| Risk / Soru | Not |
|-------------|-----|
| Gemini ücretsiz katman rate limiti | Demo trafiğinde yeterli mi? Gerekirse caching / basit gate. |
| Karmaşık sorgularda SQL doğruluğu | Few-shot örnekler + iyi şema promptu ile artırılır. |
| LSTM tahmin gücü sınırlı | Portfolyoda "entegrasyon gösterimi" olarak konumlandır. |
| Railway ücretsiz kaynak limitleri | Postgres boyutu / uptime kontrol edilmeli. |
| Türkçe soru → İngilizce şema/yanıt | Kullanıcı Türkçe sorabilir; agent İngilizce şemaya eşleyip **v1'de İngilizce özet** döner (Bölüm 9.3). Prompt'ta ele alınacak. |

---

## 16. Öğrenme Hedefi Entegrasyonu (SQL)

Bu proje bir öğrenme aracı olduğundan, geliştirme boyunca:
- Agent'ın ürettiği her SQL, UI'daki **açıklama panelinde** insan diliyle açıklanır (JOIN neden gerekli, window function ne yapıyor, GROUP BY mantığı vb.).
- Geliştirme sırasında yeni bir SQL kavramı (CTE, window function, aggregate, date_trunc, vb.) ilk kez kullanıldığında dokümante edilir.
- `docs/sql-notes.md` dosyasında öğrenilen kalıplar biriktirilir.

---

*Bu PRD yaşayan bir dokümandır; geliştirme ilerledikçe güncellenecektir.*
