-- =====================================================================
-- Gün 3 — JOIN türleri, GROUP BY, aggregate, date_trunc
-- =====================================================================

-- 1) INNER JOIN — sadece her iki tarafta da eşleşmesi olan satırlar
SELECT o.order_id, o.order_purchase_timestamp, oi.product_id, oi.price
FROM olist_orders o
JOIN olist_order_items oi ON o.order_id = oi.order_id
LIMIT 5;


-- 2) INNER JOIN vs LEFT JOIN — kaç sipariş kayboluyor?
--    Sonuç: 99.441 toplam, 98.666 INNER JOIN'de var → 775 sipariş kalemsiz.
SELECT
  (SELECT COUNT(*) FROM olist_orders) AS toplam_siparis,
  (SELECT COUNT(DISTINCT o.order_id)
   FROM olist_orders o
   JOIN olist_order_items oi ON o.order_id = oi.order_id) AS inner_join_siparis,
  (SELECT COUNT(DISTINCT o.order_id)
   FROM olist_orders o
   LEFT JOIN olist_order_items oi ON o.order_id = oi.order_id) AS left_join_siparis;


-- 3) LEFT JOIN + IS NULL — eşleşmeyen satırları bul (anti-join kalıbı)
--    Bulgu: hepsi 'unavailable' veya 'canceled' durumunda.
SELECT o.order_id, o.order_status, oi.product_id, oi.price
FROM olist_orders o
LEFT JOIN olist_order_items oi ON o.order_id = oi.order_id
WHERE oi.order_id IS NULL
LIMIT 5;


-- 4) Kategori bazlı gelir — 3 JOIN zinciri + GROUP BY + aggregate
--    Dikkat: INNER JOIN kullanıyor, 13 ürün (çevirisi olmayan kategori)
--    sessizce dışarıda kalıyor (bkz. sorgu 6).
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


-- 4b) HAVING — WHERE gruplamadan önce çalıştığı için COUNT(*) > 3000 gibi
--     bir koşulu WHERE'e yazamayız; HAVING gruplamadan sonra filtreler.
SELECT
  t.product_category_name_english AS kategori,
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


-- 5) Aylık gelir zaman serisi — date_trunc
--    Dikkat: 2016-11 ayı seride yok (o ay hiç teslimat olmamış).
--    GROUP BY sadece var olan grupları döndürür, boşluğu doldurmaz.
SELECT
  date_trunc('month', o.order_purchase_timestamp)::date AS ay,
  COUNT(DISTINCT o.order_id) AS siparis_sayisi,
  SUM(oi.price) AS aylik_gelir
FROM olist_orders o
JOIN olist_order_items oi ON o.order_id = oi.order_id
WHERE o.order_status = 'delivered'
GROUP BY ay
ORDER BY ay;


-- 6) Veri kalitesi kontrolü — hangi kategori kodlarının çevirisi yok?
--    LEFT JOIN + IS NULL kalıbı burada da işe yarıyor.
SELECT p.product_category_name, COUNT(*)
FROM olist_products p
LEFT JOIN product_category_name_translation t ON t.product_category_name = p.product_category_name
WHERE t.product_category_name IS NULL
GROUP BY p.product_category_name;


-- =====================================================================
-- KENDİN DENE
-- =====================================================================

-- a) Şehir bazında (customer_city) toplam sipariş sayısı, ilk 10 (en çoktan aza)
--    (ipucu: olist_orders JOIN olist_customers, GROUP BY customer_city)

-- b) Her satıcının (seller) toplam kaç ürün sattığı ve toplam geliri
--    (ipucu: olist_order_items JOIN olist_sellers, GROUP BY seller_id)

-- c) HAVING kullanarak: sadece 100'den fazla kalem satan kategoriler
--    (ipucu: GROUP BY ... HAVING COUNT(*) > 100)

-- d) Yıl bazında (date_trunc('year', ...)) toplam gelir
