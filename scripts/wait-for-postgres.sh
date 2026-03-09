#!/bin/bash
# Wait for PostgreSQL to be ready

set -e

host="$1"
port="$2"
user="$3"
database="$4"
timeout="${5:-30}"

echo "Waiting for PostgreSQL at $host:$port..."

for i in $(seq 1 $timeout); do
    if pg_isready -h "$host" -p "$port" -U "$user" -d "$database" 2>/dev/null; then
        echo "PostgreSQL is ready!"
        exit 0
    fi
    echo "PostgreSQL is unavailable - sleeping (attempt $i/$timeout)"
    sleep 2
done

echo "PostgreSQL failed to become ready within $timeout seconds"
exit 1
