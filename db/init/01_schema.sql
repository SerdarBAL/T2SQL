-- Olist şeması (Postgres 16)
-- Not: Kaynak CSV'ler ham veri; bazı tablolarda tekrar eden satırlar var
-- (geolocation, order_reviews) — bu yüzden oralarda PK tanımlamıyoruz.

CREATE TABLE olist_customers (
    customer_id              TEXT PRIMARY KEY,
    customer_unique_id       TEXT NOT NULL,
    customer_zip_code_prefix INTEGER,
    customer_city            TEXT,
    customer_state           CHAR(2)
);

CREATE TABLE olist_sellers (
    seller_id              TEXT PRIMARY KEY,
    seller_zip_code_prefix INTEGER,
    seller_city            TEXT,
    seller_state           CHAR(2)
);

CREATE TABLE olist_products (
    product_id                 TEXT PRIMARY KEY,
    product_category_name      TEXT,
    product_name_lenght        INTEGER,   -- CSV'deki yazım hatası korundu
    product_description_lenght INTEGER,
    product_photos_qty         INTEGER,
    product_weight_g           INTEGER,
    product_length_cm          INTEGER,
    product_height_cm          INTEGER,
    product_width_cm           INTEGER
);

CREATE TABLE olist_orders (
    order_id                      TEXT PRIMARY KEY,
    customer_id                   TEXT REFERENCES olist_customers(customer_id),
    order_status                  TEXT,
    order_purchase_timestamp      TIMESTAMP,
    order_approved_at             TIMESTAMP,
    order_delivered_carrier_date  TIMESTAMP,
    order_delivered_customer_date TIMESTAMP,
    order_estimated_delivery_date TIMESTAMP
);

CREATE TABLE olist_order_items (
    order_id            TEXT REFERENCES olist_orders(order_id),
    order_item_id       INTEGER,
    product_id          TEXT REFERENCES olist_products(product_id),
    seller_id           TEXT REFERENCES olist_sellers(seller_id),
    shipping_limit_date TIMESTAMP,
    price               NUMERIC(10,2),
    freight_value       NUMERIC(10,2),
    PRIMARY KEY (order_id, order_item_id)
);

CREATE TABLE olist_order_payments (
    order_id             TEXT REFERENCES olist_orders(order_id),
    payment_sequential   INTEGER,
    payment_type         TEXT,
    payment_installments INTEGER,
    payment_value        NUMERIC(10,2),
    PRIMARY KEY (order_id, payment_sequential)
);

CREATE TABLE olist_order_reviews (
    review_id               TEXT,
    order_id                TEXT,
    review_score            INTEGER,
    review_comment_title    TEXT,
    review_comment_message  TEXT,
    review_creation_date    TIMESTAMP,
    review_answer_timestamp TIMESTAMP
);

CREATE TABLE olist_geolocation (
    geolocation_zip_code_prefix INTEGER,
    geolocation_lat             DOUBLE PRECISION,
    geolocation_lng             DOUBLE PRECISION,
    geolocation_city            TEXT,
    geolocation_state           CHAR(2)
);

CREATE TABLE product_category_name_translation (
    product_category_name         TEXT PRIMARY KEY,
    product_category_name_english TEXT
);

-- Sık kullanılacak sorgu kalıpları için indeksler
CREATE INDEX idx_orders_purchase_ts ON olist_orders (order_purchase_timestamp);
CREATE INDEX idx_orders_status      ON olist_orders (order_status);
CREATE INDEX idx_items_product      ON olist_order_items (product_id);
CREATE INDEX idx_items_seller       ON olist_order_items (seller_id);
CREATE INDEX idx_reviews_order      ON olist_order_reviews (order_id);
