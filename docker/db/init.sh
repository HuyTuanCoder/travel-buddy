#!/bin/sh
set -e

create_schema() {
  role="$1"
  password="$2"
  schema="$3"

  if [ -z "$role" ] || [ -z "$password" ]; then
    echo "Skipping schema '$schema' (missing role or password)"
    return 0
  fi

  psql -v ON_ERROR_STOP=1 \
    --username "$POSTGRES_USER" \
    --dbname "$POSTGRES_DB" \
    -v role="$role" \
    -v password="$password" \
    -v schema="$schema" \
    <<'SQL'
    SELECT format('CREATE ROLE %I LOGIN PASSWORD %L', :'role', :'password')
    WHERE NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = :'role')
    \gexec

    SELECT format('CREATE SCHEMA IF NOT EXISTS %I AUTHORIZATION %I', :'schema', :'role')
    \gexec

    SELECT format('GRANT USAGE, CREATE ON SCHEMA %I TO %I', :'schema', :'role')
    \gexec
SQL
}

create_schema "$AUTH_DB_USER" "$AUTH_DB_PASSWORD" "auth"
create_schema "$USER_DB_USER" "$USER_DB_PASSWORD" "app_user"
create_schema "$EXPENSE_DB_USER" "$EXPENSE_DB_PASSWORD" "expense"
create_schema "$ITINERARY_DB_USER" "$ITINERARY_DB_PASSWORD" "itinerary"
create_schema "$LOCATION_DB_USER" "$LOCATION_DB_PASSWORD" "location"
create_schema "$NOTIFICATION_DB_USER" "$NOTIFICATION_DB_PASSWORD" "notification"

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-SQL
  REVOKE ALL ON SCHEMA public FROM PUBLIC;
SQL
