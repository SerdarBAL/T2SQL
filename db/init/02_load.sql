-- Olist CSV'lerini yükle.
-- Sıralama önemli: foreign key'lerin işaret ettiği tablolar önce dolmalı.
-- COPY server-side çalışır; dosyalar container'a /data/raw olarak mount edilmiştir.
-- Tırnaksız boş alan ("a,,b") otomatik olarak NULL kabul edilir.

\echo 'Loading olist_customers...'
COPY olist_customers FROM '/data/raw/olist_customers_dataset.csv'
    WITH (FORMAT csv, HEADER true);

\echo 'Loading olist_sellers...'
COPY olist_sellers FROM '/data/raw/olist_sellers_dataset.csv'
    WITH (FORMAT csv, HEADER true);

\echo 'Loading olist_products...'
COPY olist_products FROM '/data/raw/olist_products_dataset.csv'
    WITH (FORMAT csv, HEADER true);

\echo 'Loading olist_orders...'
COPY olist_orders FROM '/data/raw/olist_orders_dataset.csv'
    WITH (FORMAT csv, HEADER true);

\echo 'Loading olist_order_items...'
COPY olist_order_items FROM '/data/raw/olist_order_items_dataset.csv'
    WITH (FORMAT csv, HEADER true);

\echo 'Loading olist_order_payments...'
COPY olist_order_payments FROM '/data/raw/olist_order_payments_dataset.csv'
    WITH (FORMAT csv, HEADER true);

\echo 'Loading olist_order_reviews...'
COPY olist_order_reviews FROM '/data/raw/olist_order_reviews_dataset.csv'
    WITH (FORMAT csv, HEADER true);

\echo 'Loading olist_geolocation...'
COPY olist_geolocation FROM '/data/raw/olist_geolocation_dataset.csv'
    WITH (FORMAT csv, HEADER true);

\echo 'Loading product_category_name_translation...'
COPY product_category_name_translation FROM '/data/raw/product_category_name_translation.csv'
    WITH (FORMAT csv, HEADER true);

-- Planner'ın doğru karar vermesi için istatistikleri güncelle
ANALYZE;

\echo '--- Satır sayıları ---'
SELECT 'olist_customers' AS table_name, count(*) FROM olist_customers
UNION ALL SELECT 'olist_sellers', count(*) FROM olist_sellers
UNION ALL SELECT 'olist_products', count(*) FROM olist_products
UNION ALL SELECT 'olist_orders', count(*) FROM olist_orders
UNION ALL SELECT 'olist_order_items', count(*) FROM olist_order_items
UNION ALL SELECT 'olist_order_payments', count(*) FROM olist_order_payments
UNION ALL SELECT 'olist_order_reviews', count(*) FROM olist_order_reviews
UNION ALL SELECT 'olist_geolocation', count(*) FROM olist_geolocation
UNION ALL SELECT 'product_category_name_translation', count(*) FROM product_category_name_translation
ORDER BY 1;
