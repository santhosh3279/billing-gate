#!/bin/sh
set -e

# Default data dir
DATA_DIR="${DATA_DIR:-/var/lib/billing-gate}"

# Ensure data directory exists
mkdir -p "$DATA_DIR"

# If running as root, fix ownership so non-root 'node' user can read/write data
if [ "$(id -u)" = '0' ]; then
    chown -R node:node "$DATA_DIR"
    chmod 700 "$DATA_DIR"
    
    # If first argument is 'node' or 'npm', execute with su-exec as node user
    if [ "$1" = 'node' ] || [ "$1" = 'npm' ]; then
        exec su-exec node "$@"
    fi
fi

exec "$@"
