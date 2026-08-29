#!/usr/bin/env bash
# ==============================================================================
# console.sh
# Serial terminal console helper for ARM Embedded Linux Lab monorepo.
# ==============================================================================

set -euo pipefail

BOARD=""
SERIAL_PORT=""
SERIAL_BAUD="115200"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --board=*) BOARD="${1#*=}" ;;
    --serial-port=*) SERIAL_PORT="${1#*=}" ;;
    --serial-baud=*) SERIAL_BAUD="${1#*=}" ;;
    -h|--help)
      echo "Usage: $0 --board=<name> [--serial-port=<port>] [--serial-baud=<baud>]"
      exit 0
      ;;
    *)
      echo "[ERROR] Unknown option: $1"
      exit 1
      ;;
  esac
  shift
done

if [ -z "$SERIAL_PORT" ]; then
  echo "[ERROR] BOARD_SERIAL_PORT is not set. Please configure tools/deploy/boards/${BOARD}.env"
  exit 1
fi

if [ ! -e "$SERIAL_PORT" ]; then
  echo "[ERROR] Serial device '$SERIAL_PORT' not found on this host."
  exit 1
fi

echo "[INFO] Connecting to ${BOARD} on ${SERIAL_PORT} (${SERIAL_BAUD} baud)..."
echo "[INFO] To exit picocom: Ctrl+A followed by Ctrl+X"

if command -v picocom >/dev/null 2>&1; then
  exec picocom -b "$SERIAL_BAUD" "$SERIAL_PORT"
elif command -v minicom >/dev/null 2>&1; then
  exec minicom -D "$SERIAL_PORT" -b "$SERIAL_BAUD"
elif command -v screen >/dev/null 2>&1; then
  exec screen "$SERIAL_PORT" "$SERIAL_BAUD"
else
  echo "[ERROR] No serial terminal emulator found (picocom, minicom, or screen required)."
  exit 1
fi
