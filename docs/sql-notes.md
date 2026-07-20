# SQL Öğrenme Notları (T2SQL)

Bu dosya proje boyunca öğrendiğim SQL kavramlarını biriktirir. Hedef: proje sonunda
"bir AI engineer'ın ihtiyaç duyduğu kadar SQL biliyorum" diyebilmek.

---

## Gün 1 — Veri setini tanıma

### Olist veri modeli (özet)
Olist, Brezilya'nın en büyük e-ticaret pazaryerlerinden birinin ~100k gerçek siparişini
içerir. Tablolar `order_id`, `product_id`, `customer_id`, `seller_id` gibi anahtarlarla
birbirine bağlanır.

| Tablo | İçerik | Ana anahtar / bağlantı |
|-------|--------|------------------------|
| `olist_orders` | Siparişler, tarih, durum | `order_id` (PK), `customer_id` |
| `olist_order_items` | Sipariş kalemleri, fiyat, kargo | `order_id` + `order_item_id`, `product_id`, `seller_id` |
| `olist_products` | Ürünler, kategori | `product_id` (PK) |
| `olist_customers` | Müşteriler, şehir/eyalet | `customer_id` (PK) |
| `olist_sellers` | Satıcılar | `seller_id` (PK) |
| `olist_order_payments` | Ödemeler | `order_id`, `payment_value` |
| `olist_order_reviews` | Yorum puanları | `order_id`, `review_score` |
| `product_category_name_translation` | Kategori adı PT→EN | `product_category_name` |

**Kilit fikir:** "Gelir" tek bir kolonda yok. Gelir = `olist_order_items.price` toplamı;
zaman bilgisi `olist_orders.order_purchase_timestamp`'ten gelir. İkisini `order_id`
üzerinden `JOIN` etmek, projedeki en temel ve en sık kullanılacak kalıp.

> Sorgu örnekleri Gün 2–3'te (Postgres kurulduktan sonra) buraya eklenecek.

---

<!-- Sonraki günlerin notları buraya eklenecek: JOIN türleri, GROUP BY, aggregate,
     date_trunc, window functions, CTE, vb. -->
