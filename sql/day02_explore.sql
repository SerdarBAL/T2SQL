-- =====================================================================
-- Gün 2 — SELECT temelleri (keşif sorguları)
-- SQLTools'ta çalıştırmak için: sorgunun üstündeki "Run on active connection"
-- linkine tıkla, ya da imleci sorgunun içine koyup Ctrl+E Ctrl+E bas.
-- =====================================================================

-- 1) DISTINCT — kaç farklı sipariş durumu var?
--    Yeni bir tabloyla tanışırken ilk sorulacak soru.
SELECT DISTINCT order_status
FROM olist_orders
ORDER BY order_status;


-- 2) WHERE + ORDER BY + LIMIT — en pahalı 5 sipariş kalemi
--    Keşif sorgularında LIMIT'i alışkanlık yap.
SELECT order_id, product_id, price
FROM olist_order_items
WHERE price > 1000
ORDER BY price DESC
LIMIT 5;


-- 3) Toplama fonksiyonları — veri hangi aralığı kapsıyor?
--    GROUP BY olmadan tüm tablo tek grup sayılır: 99.441 satır → 1 satır.
SELECT MIN(order_purchase_timestamp) AS ilk_siparis,
       MAX(order_purchase_timestamp) AS son_siparis,
       COUNT(*)                      AS toplam_siparis
FROM olist_orders;


-- 4) Tarih aralığı — BETWEEN yerine >= ... AND < kalıbı
--    Kolon TIMESTAMP olduğu için BETWEEN son günün saatlerini kaçırır.
SELECT COUNT(*) AS ekim_2018_siparis
FROM olist_orders
WHERE order_purchase_timestamp >= '2018-10-01'
  AND order_purchase_timestamp <  '2018-11-01';


-- 5) NULL — "= NULL" çalışmaz, "IS NULL" yazılır
SELECT COUNT(*) AS kategorisiz_urun
FROM olist_products
WHERE product_category_name IS NULL;


-- 6) COUNT(*) vs COUNT(kolon) — aradaki fark tam olarak NULL sayısıdır
SELECT COUNT(*)                     AS tum_satirlar,      -- 32951
       COUNT(product_category_name) AS kategorisi_olanlar -- 32341
FROM olist_products;


-- 7) Şema keşfi — psql'in \dt komutunun SQL karşılığı
--    information_schema standarttır; Faz 1'deki fetch_schema düğümü buna benzer
--    bir sorgu atacak (LLM'e şema bilgisini vermek için).
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
ORDER BY table_name;


-- 8) Tek tablonun kolonları — \d olist_orders karşılığı
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'olist_orders'
ORDER BY ordinal_position;


-- =====================================================================
-- KENDİN DENE (cevapları yarın JOIN'lerle genişleteceğiz)
-- =====================================================================

-- a) Kaç farklı ödeme tipi var?  (ipucu: DISTINCT, olist_order_payments)

-- b) En ucuz 10 sipariş kalemi hangileri?  (ipucu: ORDER BY ... ASC)

-- c) 2017 yılında kaç sipariş verilmiş?  (ipucu: 4 numaralı kalıp)

-- d) Teslim tarihi girilmemiş kaç sipariş var?
--    (ipucu: order_delivered_customer_date IS NULL)

-- e) SP eyaletinde kaç müşteri kayıtlı?  (ipucu: olist_customers, WHERE)
