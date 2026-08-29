#!/usr/bin/env bash
# ==============================================================================
# gdb.sh
# Cross-GDB launcher helper for ARM Embedded Linux Lab monorepo.
# ==============================================================================

set -euo pipefail

TARGET_ELF=""
CROSS_GDB="gdb-multiarch"
TARGET_IP=""
GDB_PORT="2345"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --target-elf=*) TARGET_ELF="${1#*=}" ;;
    --cross-gdb=*) CROSS_GDB="${1#*=}" ;;
    --target-ip=*) TARGET_IP="${1#*=}" ;;
    --gdb-port=*) GDB_PORT="${1#*=}" ;;
    -h|--help)
      echo "Usage: $0 --target-elf=<path> [--target-ip=<ip>] [--gdb-port=<port>]"
      exit 0
      ;;
    *)
      echo "[ERROR] Unknown option: $1"
      exit 1
      ;;
  esac
  shift
done

if [ -z "$TARGET_ELF" ] || [ ! -f "$TARGET_ELF" ]; then
  echo "[ERROR] Target ELF binary '$TARGET_ELF' not found."
  exit 1
fi

# Locate suitable GDB client
GDB_BIN=""
if command -v "$CROSS_GDB" >/dev/null 2>&1; then
  GDB_BIN="$CROSS_GDB"
elif command -v gdb-multiarch >/dev/null 2>&1; then
  GDB_BIN="gdb-multiarch"
elif command -v gdb >/dev/null 2>&1; then
  GDB_BIN="gdb"
else
  echo "[ERROR] No suitable GDB executable found (checked '$CROSS_GDB', 'gdb-multiarch', 'gdb')."
  exit 1
fi

echo "[INFO] Using GDB: $GDB_BIN"
echo "[INFO] Target binary: $TARGET_ELF"

if [ -n "$TARGET_IP" ]; then
  echo "[INFO] Auto-connecting to target remote $TARGET_IP:$GDB_PORT..."
  exec "$GDB_BIN" \
    -ex "set architecture arm64" \
    -ex "target remote $TARGET_IP:$GDB_PORT" \
    "$TARGET_ELF"
else
  echo "[INFO] TARGET_IP not specified. Starting GDB in local mode..."
  exec "$GDB_BIN" "$TARGET_ELF"
fi
