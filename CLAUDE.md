# CLAUDE.md — T2SQL Projesi

Agentic Text-to-SQL analitik & öngörü platformu. Detaylı gereksinimler `prd.md`, günlük plan `plan.md`.

## İletişim
- Kullanıcı (Serdar) ile **sohbet Türkçe** olmalı.
- Bu bir **öğrenme projesi**: SQL üretilirken/kullanılırken kullanıcıya öğretici biçimde **SQL açıkla**. Yeni SQL kavramları `docs/sql-notes.md`'ye kaydedilir.
- İki bitiş hedefi: (1) AI engineer düzeyinde SQL, (2) güçlü deployment becerisi.

## Ürün Dili
- **v1 için UI metinleri ve agent özet (summary) çıktısı İngilizce** (PRD Bölüm 9.3). Çok dilli destek v2.

## Stack (kesin)
- **LLM:** Gemini API (`langchain-google-genai`), provider-agnostic katman. (Claude Pro API olarak kullanılamaz.)
- **Frontend:** Next.js 14 + React + TS + Tailwind + shadcn/ui + Framer Motion + Plotly.js
- **Backend:** FastAPI + LangGraph + LangChain + SQLAlchemy/psycopg (SSE streaming)
- **DB:** PostgreSQL 16, **Olist** dataset (read-only rol, yalnızca SELECT, statement timeout)
- **Deploy:** Docker + Docker Compose + GitHub Actions CI/CD + Railway

## Fazlar (başlangıç Pzt 20 Tem 2026, ~25 gün, tahmini bitiş 13 Ağu)

| Faz | Günler | Tarih | Konu | Çıktı |
|-----|--------|-------|------|-------|
| **0 — Kurulum & Veri** | 1–3 | 20–22 Tem | Repo iskeleti, Olist'i Postgres'e yükleme, SQL temelleri (SELECT/WHERE → JOIN/GROUP BY/aggregate → date_trunc) | Dolu Olist DB |
| **1 — Agent Çekirdeği** | 4–9 | 23–28 Tem | FastAPI + Gemini, LangGraph (classify→schema→generate→validate→execute), **self-correction döngüsü** (max 3), summarize, window fonksiyonları | Soru → SQL → doğru sonuç |
| **2 — Görselleştirme** | 10–11 | 29–30 Tem | `viz_spec` üretimi (bar/line/pie/table), `/api/chat` SSE streaming | Grafik/tablo döndüren API |
| **3 — Frontend** | 12–16 | 31 Tem–4 Ağu | Next.js chat UI, streaming render, stepper, dinamik tablo (Framer Motion), Plotly paneli, SQL açıklama paneli, tema | Çalışan profesyonel UI |
| **4 — LSTM** | 17–18 | 5–6 Ağu | Offline gelir zaman serisi eğitimi (PyTorch), inference düğümü, geçmiş+tahmin grafiği | Gelir tahmini canlı |
| **5 — DevOps ⭐** | 19–23 | 7–11 Ağu | Multi-stage Docker, tam yığın compose, GitHub Actions CI (lint+test+build), Railway deploy (managed Postgres + backend + frontend), CD | Public URL'de canlı + CI/CD |
| **6 — Cila & Portfolyo** | 24–25 | 12–13 Ağu | UX cila, rate limiting, README + mimari diyagram + demo GIF/video, sql-notes derleme | Portfolyoya hazır |

**Buffer/dinlenme günleri:** 7. gün (26 Tem), 14. gün (2 Ağu), 21. gün (9 Ağu).
**Kritik yol:** Faz 1 (agent) ve Faz 3 (frontend) — en uzun/riskli kısımlar.

Her fazın sonunda commit + kısa demo. Bu plan yaşayan dokümandır; ilerledikçe güncellenir.
