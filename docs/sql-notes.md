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

---

## Gün 2 — Postgres kurulumu + `SELECT` temelleri

Veri artık Docker'daki Postgres 16'da. Bağlanmak için:

```bash
docker compose exec postgres psql -U t2sql -d olist
```

`psql` içinde işe yarayan meta komutlar (bunlar SQL değil, psql'in kendi komutları):

| Komut | İş |
|-------|-----|
| `\dt` | Tabloları listele |
| `\d olist_orders` | Tek tablonun kolonları, tipleri, indeksleri |
| `\du` | Rolleri (kullanıcıları) listele |
| `\q` | Çık |

### Sorgunun okunma sırası ≠ yazılma sırası

Bu, SQL'i "anlamanın" anahtarı. Sen şu sırayla yazarsın:

```sql
SELECT ... FROM ... WHERE ... ORDER BY ... LIMIT ...
```

Ama veritabanı şu sırayla **çalıştırır**:

```
FROM      → hangi tablodan?
WHERE     → hangi satırlar kalsın?      (satır filtresi)
SELECT    → hangi kolonlar dönsün?      (kolon seçimi)
ORDER BY  → nasıl sıralansın?
LIMIT     → kaç tanesi dönsün?
```

Bunu bilmek ileride işine yarayacak: `SELECT`'te verdiğin bir takma adı (`AS`)
`WHERE` içinde neden kullanamadığını açıklar — `WHERE` çalıştığında o takma ad
henüz var olmamıştır.

### `DISTINCT` — benzersiz değerler

```sql
SELECT DISTINCT order_status FROM olist_orders ORDER BY order_status;
```

8 durum döndü: `approved`, `canceled`, `created`, `delivered`, `invoiced`,
`processing`, `shipped`, `unavailable`.

Yeni bir tabloyla tanışırken ilk yapılacak şey budur: kategorik bir kolonun
kaç farklı değeri var? Burada öğrendiğimiz kritik bilgi — `delivered` dışında
durumlar da var, yani **gelir hesaplarken filtre gerekecek**.

### `WHERE` + `ORDER BY` + `LIMIT`

```sql
SELECT order_id, product_id, price
FROM olist_order_items
WHERE price > 1000
ORDER BY price DESC
LIMIT 5;
```

- `WHERE` satırları eler (kolonları değil).
- `ORDER BY ... DESC` büyükten küçüğe. `ASC` varsayılan, yazmasan da olur.
- `LIMIT 5` ilk 5 satır. **Her keşif sorgusunda `LIMIT` kullan** — 1M satırlık
  `olist_geolocation`'da `LIMIT`siz `SELECT *` yazarsan terminal boğulur.

En pahalı kalem R$6.735. Ortalama fiyatın R$120 olduğunu düşünürsek bu ciddi bir
uç değer — ortalama alırken aklında olsun.

### Toplama fonksiyonları (`MIN` / `MAX` / `COUNT`)

```sql
SELECT MIN(order_purchase_timestamp) AS ilk,
       MAX(order_purchase_timestamp) AS son,
       COUNT(*) AS siparis
FROM olist_orders;
```

→ `2016-09-04` … `2018-10-17`, 99.441 sipariş.

Bu sorgu **99.441 satırı tek satıra indirir**. `GROUP BY` olmadan bir toplama
fonksiyonu kullandığında, tüm tablo tek bir grup sayılır. Yarın `GROUP BY` ile
bunu "her ay için ayrı ayrı" yapmayı öğreneceğiz.

`AS` takma ad (alias) verir; sonucun kolon başlığını okunur yapar.

### Tarih filtreleme

```sql
SELECT COUNT(*) AS kasim_2018
FROM olist_orders
WHERE order_purchase_timestamp >= '2018-11-01'
  AND order_purchase_timestamp <  '2018-12-01';
```

→ `0`. Çünkü veri 2018-10-17'de bitiyor.

**Neden `>=` ve `<`, neden `BETWEEN` değil?** `BETWEEN '2018-11-01' AND '2018-11-30'`
yazarsan, 30 Kasım saat 00:00:00'dan sonraki siparişleri kaçırırsın — çünkü kolon
`TIMESTAMP` (saat içeriyor), `'2018-11-30'` ise `2018-11-30 00:00:00` demek.
`>= başlangıç AND < sonraki_ayın_başı` kalıbı bu tuzağa hiç düşmez. Tarih
aralıklarında bunu alışkanlık edin.

### `NULL` ile çalışmak

```sql
SELECT COUNT(*) AS kategorisiz
FROM olist_products
WHERE product_category_name IS NULL;
```

→ 610 ürün.

**`= NULL` çalışmaz, `IS NULL` yazılır.** `NULL` "bilinmeyen" demektir, bir değer
değil. "Bilinmeyen = bilinmeyen" sorusunun cevabı `true` değil, yine `NULL`'dur.
Bu yüzden SQL ayrı bir operatör verir: `IS NULL` / `IS NOT NULL`.

`COUNT(*)` ile `COUNT(kolon)` farkı da buradan gelir: `COUNT(*)` satırları sayar,
`COUNT(product_category_name)` ise `NULL` olmayanları sayar. İkisi 610 fark verir.

### Kurulumun doğrulanması

Yükleme sonrası 9 tablonun satır sayısı, CSV'lerden pandas ile hesaplanan sayılarla
birebir tuttu (99.441 sipariş / 112.650 kalem / 1.000.163 geolocation …). Satır
kaybı yok.

Salt-okunur rol de test edildi:

```sql
SELECT count(*) FROM olist_orders;   -- ✅ 99441
DELETE FROM olist_orders;            -- ❌ ERROR: permission denied for table
DROP TABLE olist_orders;             -- ❌ ERROR: must be owner of table
```

Bu, agent'ın `validate_sql` filtresinin **arkasındaki ikinci savunma hattı**
(defense in depth). Filtre atlatılsa bile veritabanı yazma işlemini reddediyor.

---

## Gün 3 — `JOIN` türleri, `GROUP BY`, aggregate, `date_trunc`

### `INNER JOIN` vs `LEFT JOIN`

```sql
SELECT o.order_id, oi.product_id, oi.price
FROM olist_orders o
JOIN olist_order_items oi ON o.order_id = oi.order_id;
```

`JOIN` tek başına yazılınca `INNER JOIN` demektir: **yalnızca her iki tarafta da
eşleşmesi olan** satırlar döner. Test ettik:

| | satır sayısı |
|---|---|
| `olist_orders` toplam | 99.441 |
| `orders` INNER JOIN `order_items` (distinct order_id) | 98.666 |
| `orders` LEFT JOIN `order_items` (distinct order_id) | 99.441 |

Aradaki 775 sipariş `order_items`'ta hiç kalem içermiyor — durumları `unavailable`
veya `canceled`. `LEFT JOIN` sol taraftaki (`FROM`'daki) tüm satırları korur,
sağ tarafta eşleşme yoksa o kolonlar `NULL` gelir.

**Kural:** "eksiksiz" bir sayım/liste istiyorsan `LEFT JOIN`; "sadece gerçekten
ilişkili olanlar" istiyorsan `INNER JOIN`. `WHERE sag_tablo.kolon IS NULL` kalıbı,
LEFT JOIN'de eşleşmeyen satırları bulmaya yarar (bir tür anti-join).

### INNER JOIN veri kaybını sessizce yapar — kanıtlanmış tuzak

4 tabloyu (`order_items → orders → products → category_translation`) hepsi
`INNER JOIN` ile birleştirip kategori bazlı gelir hesapladık. Sonuç hatasız
döndü ama **eksikti**: `product_category_name_translation` tablosunda karşılığı
olmayan 2 kategori kodu var (`portateis_cozinha_e_preparadores_de_alimentos`,
`pc_gamer` — toplam 13 ürün) + 610 üründe kategori zaten `NULL`. Bu 13 ürünün
geliri INNER JOIN yüzünden sonuçtan sessizce düştü — sorgu hata vermedi, sadece
eksik veri döndürdü.

**Ders:** `INNER JOIN` zincirlerinde veri kaybı fark edilmez, çünkü sorgu her
zaman "başarılı" görünür. Şüpheli JOIN'leri `LEFT JOIN` ile deneyip
`WHERE sag.kolon IS NULL` ile ne kaybettiğini görmek iyi bir alışkanlık.

### `GROUP BY` + aggregate: kategori bazlı gelir

```sql
SELECT
  t.product_category_name_english AS kategori,
  COUNT(*) AS kalem_sayisi,
  SUM(oi.price) AS toplam_gelir,
  ROUND(AVG(oi.price), 2) AS ortalama_fiyat
FROM olist_order_items oi
JOIN olist_orders o ON o.order_id = oi.order_id
JOIN olist_products p ON p.product_id = oi.product_id
JOIN product_category_name_translation t ON t.product_category_name = p.product_category_name
WHERE o.order_status = 'delivered'
GROUP BY t.product_category_name_english
ORDER BY toplam_gelir DESC
LIMIT 10;
```

- `GROUP BY` tabloyu, belirtilen kolonun her benzersiz değeri için bir "kova"ya
  ayırır; aggregate fonksiyonlar (`COUNT`, `SUM`, `AVG`) artık tüm tablo yerine
  her kova için ayrı ayrı hesaplanır.
- **Kural:** `SELECT` listesindeki her kolon ya `GROUP BY`'da olmalı ya da bir
  aggregate fonksiyonun içinde olmalı — üçüncü seçenek yok, Postgres zorlar.
- Sonuç: `health_beauty` en yüksek toplam gelire sahip (R$1.23M), ama
  `watches_gifts` çok daha az kalem satıp (5.859 vs 9.465) neredeyse aynı geliri
  yapmış — çünkü ortalama fiyatı çok daha yüksek (R$199 vs R$130). Toplam gelir
  ile hacim (kalem sayısı) farklı şeyler; ikisini birlikte okumak gerekir.

### `HAVING` — `WHERE`'in yapamadığı filtre

```sql
SELECT t.product_category_name_english AS kategori,
       COUNT(*) AS kalem_sayisi,
       SUM(oi.price) AS toplam_gelir
FROM olist_order_items oi
JOIN olist_orders o ON o.order_id = oi.order_id
JOIN olist_products p ON p.product_id = oi.product_id
JOIN product_category_name_translation t ON t.product_category_name = p.product_category_name
WHERE o.order_status = 'delivered'
GROUP BY t.product_category_name_english
HAVING COUNT(*) > 3000
ORDER BY toplam_gelir DESC;
```

Çalışma sırası: `FROM → WHERE → GROUP BY → HAVING → SELECT → ORDER BY`. `WHERE`,
`GROUP BY`'dan **önce** çalışır — henüz kovalar oluşmadan, ham satırları filtreler.
`COUNT(*) > 3000` gibi bir koşul ise ancak kovalar oluştuktan sonra anlamlıdır,
bu yüzden `WHERE` içine yazılamaz (hata verir). `HAVING`, `GROUP BY`'dan **sonra**
çalışıp aggregate sonuçlara göre filtreler — `WHERE`'in tam ihtiyaç duyduğu yerde
duramadığı boşluğu doldurur.

**Özet ayrım:** `WHERE` → satır filtresi (gruplamadan önce). `HAVING` → grup
filtresi (gruplamadan sonra, aggregate'e göre).

### `date_trunc` ile aylık zaman serisi

```sql
SELECT
  date_trunc('month', o.order_purchase_timestamp)::date AS ay,
  COUNT(DISTINCT o.order_id) AS siparis_sayisi,
  SUM(oi.price) AS aylik_gelir
FROM olist_orders o
JOIN olist_order_items oi ON o.order_id = oi.order_id
WHERE o.order_status = 'delivered'
GROUP BY ay
ORDER BY ay;
```

- `date_trunc('month', ts)` bir timestamp'i ayın ilk gününe yuvarlar
  (`2017-03-15 14:22` → `2017-03-01 00:00`), böylece aynı aydaki farklı günler
  `GROUP BY`'da aynı kovaya düşer.
- `::date` tip dönüştürme (cast) — saat kısmını atıp sade tarih gösterir.

**Bulunan tuzak — eksik ay:** Seride 2016-09, 2016-10, 2016-12 var ama
**2016-11 yok** (o ay hiç teslim edilmiş sipariş olmamış — dataset pilot
dönemi). `GROUP BY` sadece verinin *var olduğu* grupları döndürür, olmayanı
atlar. LSTM'e zaman serisi verirken bu kritik: model eşit aralıklı ay bekler,
ama gerçek seri bir ay eksik gelir.

**Faz 4 için not:** `generate_series(min_tarih, max_tarih, '1 month')` ile tam
ay listesi üretip veriyle `LEFT JOIN` yapmak, eksik aylara `0` koymak gerekecek.

---

<!-- Sonraki günlerin notları buraya eklenecek: window functions, CTE, vb. -->
