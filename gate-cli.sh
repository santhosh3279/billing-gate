#!/usr/bin/env bash
set -e

# ==============================================================================
# Chettiyar Kada Billing 2FA Gate — Docker CLI Helper
#
# Usage:
#   ./gate-cli.sh add-user <username> <password>
#   ./gate-cli.sh list-users
#   ./gate-cli.sh reset-totp <username>
#   ./gate-cli.sh set-password <username> <new-password>
#   ./gate-cli.sh delete-user <username>
# ==============================================================================

CONTAINER_NAME="billing-gate"

# Ensure container is running
if ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
  echo "Error: Docker container '${CONTAINER_NAME}' is not running."
  echo "Start the container first with: docker compose up -d"
  exit 1
fi

# Detect interactive terminal for proper ANSI colors and QR code display
if [ -t 0 ] && [ -t 1 ]; then
  DOCKER_FLAGS="-it"
else
  DOCKER_FLAGS="-i"
fi

docker compose exec $DOCKER_FLAGS "${CONTAINER_NAME}" node cli.js "$@"
