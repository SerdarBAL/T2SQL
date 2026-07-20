# data/

Olist veri seti buraya (`data/raw/`) indirilir. **CSV'ler git'e commit'lenmez** (bkz. `.gitignore`).

## İndirme
1. Kaggle: https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce
2. "Download" ile ZIP'i al, içindeki CSV'leri `data/raw/` altına çıkar.

## Beklenen dosyalar (`data/raw/`)
- `olist_orders_dataset.csv`
- `olist_order_items_dataset.csv`
- `olist_products_dataset.csv`
- `olist_customers_dataset.csv`
- `olist_sellers_dataset.csv`
- `olist_order_payments_dataset.csv`
- `olist_order_reviews_dataset.csv`
- `olist_geolocation_dataset.csv`
- `product_category_name_translation.csv`

Bu CSV'ler Gün 2'de Docker Compose + seed script ile PostgreSQL'e yüklenecek.
