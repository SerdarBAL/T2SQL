#!/bin/bash
# Uygulamanın bağlanacağı SALT-OKUNUR rol (defense-in-depth).
# Agent'taki SELECT-only guard aşılsa bile bu rol yazma yapamaz.
set -euo pipefail

psql -v ON_ERROR_STOP=1 \
     --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" \
     -v ro_user="$APP_READONLY_USER" -v ro_pass="$APP_READONLY_PASSWORD" \
     -v db="$POSTGRES_DB" <<-'EOSQL'
    CREATE ROLE :"ro_user" LOGIN PASSWORD :'ro_pass';

    GRANT CONNECT ON DATABASE :"db" TO :"ro_user";
    GRANT USAGE ON SCHEMA public TO :"ro_user";
    GRANT SELECT ON ALL TABLES IN SCHEMA public TO :"ro_user";

    -- İleride eklenecek tablolar için de otomatik SELECT hakkı
    ALTER DEFAULT PRIVILEGES IN SCHEMA public
        GRANT SELECT ON TABLES TO :"ro_user";

    -- Tablo/şema oluşturma hakkını açıkça kapat
    REVOKE CREATE ON SCHEMA public FROM :"ro_user";

    -- Kaçak/uzun sorgular DB seviyesinde de kesilsin
    ALTER ROLE :"ro_user" SET statement_timeout = '10s';
EOSQL

echo "Read-only role '$APP_READONLY_USER' created."
