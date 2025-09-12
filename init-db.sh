#!/bin/bash
set -e

# Create the krishi_officer database
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE DATABASE krishi_officer;
    GRANT ALL PRIVILEGES ON DATABASE krishi_officer TO $POSTGRES_USER;
EOSQL