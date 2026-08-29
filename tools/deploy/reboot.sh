#!/usr/bin/env bash
# ==============================================================================
# reboot.sh
# Unified target reboot and reset helper for ARM Embedded Linux Lab monorepo.
#
# Supports:
# - uboot_serial: Sends reset command over UART to U-Boot console
# - ssh: Issues reboot command over SSH to Linux target
# - sysrq_serial: Sends Magic SysRq reset over serial
# - power_relay: Power-cycles USB/DC relay or smart plug
# ==============================================================================

set -euo pipefail

BOARD=""
METHOD="uboot_serial"
SERIAL_PORT=""
SERIAL_BAUD="115200"
RESET_CMD="reset\r"
TARGET_IP=""
TARGET_USER="root"
TARGET_PORT="22"
TARGET_KEY=""
DRY_RUN=false

# ANSI colors
COLOR_BLUE="\033[1;34m"
COLOR_GREEN="\033[1;32m"
COLOR_YELLOW="\033[1;33m"
COLOR_RED="\033[1;31m"
COLOR_RESET="\033[0m"

log_info()    { echo -e "${COLOR_BLUE}[REBOOT]${COLOR_RESET} $*"; }
log_success() { echo -e "${COLOR_GREEN}[SUCCESS]${COLOR_RESET} $*"; }
log_warn()    { echo -e "${COLOR_YELLOW}[WARN]${COLOR_RESET} $*"; }
log_error()   { echo -e "${COLOR_RED}[ERROR]${COLOR_RESET} $*"; }

while [[ $# -gt 0 ]]; do
  case "$1" in
    --board=*) BOARD="${1#*=}" ;;
    --method=*) METHOD="${1#*=}" ;;
    --serial-port=*) SERIAL_PORT="${1#*=}" ;;
    --serial-baud=*) SERIAL_BAUD="${1#*=}" ;;
    --reset-cmd=*) RESET_CMD="${1#*=}" ;;
    --target-ip=*) TARGET_IP="${1#*=}" ;;
    --target-user=*) TARGET_USER="${1#*=}" ;;
    --target-port=*) TARGET_PORT="${1#*=}" ;;
    --target-key=*) TARGET_KEY="${1#*=}" ;;
    --dry-run) DRY_RUN=true ;;
    -h|--help)
      echo "Usage: $0 [options]"
      echo "  --board=<name>         Board profile name"
      echo "  --method=<method>      Reboot method (uboot_serial, ssh, sysrq_serial, power_relay)"
      echo "  --serial-port=<port>   Serial device (e.g. /dev/ttyUSB0)"
      echo "  --serial-baud=<baud>   Baud rate (default: 115200)"
      echo "  --reset-cmd=<cmd>      Command string to send over serial (default: 'reset\\r')"
      echo "  --target-ip=<ip>       Target IP (for SSH method)"
      echo "  --dry-run              Simulate without sending commands"
      exit 0
      ;;
    *)
      log_error "Unknown option: $1"
      exit 1
      ;;
  esac
  shift
done

# ------------------------------------------------------------------------------
# Method Implementations
# ------------------------------------------------------------------------------

reboot_uboot_serial() {
  log_info "Attempting U-Boot reset over serial port: ${SERIAL_PORT:-<not configured>} (${SERIAL_BAUD} baud)..."
  if [ -z "$SERIAL_PORT" ]; then
    log_error "BOARD_SERIAL_PORT is not set. Please configure tools/deploy/boards/${BOARD}.env"
    return 1
  fi

  if [ "$DRY_RUN" = true ]; then
    log_info "[DRY-RUN] Would send '${RESET_CMD}' to ${SERIAL_PORT} at ${SERIAL_BAUD} baud"
    return 0
  fi

  if [ ! -e "$SERIAL_PORT" ]; then
    log_error "Serial port device $SERIAL_PORT does not exist on this host."
    return 1
  fi

  # Send reset command over serial port using python / stty
  python3 - <<EOF
import serial, time
try:
    s = serial.Serial('$SERIAL_PORT', int('$SERIAL_BAUD'), timeout=1)
    s.write(b'\r\n')
    time.sleep(0.2)
    s.write(b'$RESET_CMD\n')
    time.sleep(0.2)
    s.close()
    print("  [OK] Reset command sent successfully.")
except Exception as e:
    # Fallback to direct device redirection if pyserial is not installed
    import subprocess
    cmd = "stty -F $SERIAL_PORT $SERIAL_BAUD raw -echo && echo -e '$RESET_CMD' > $SERIAL_PORT"
    res = subprocess.run(cmd, shell=True)
    if res.returncode != 0:
        print(f"  [ERROR] Serial write failed: {e}")
        exit(1)
EOF
  log_success "U-Boot reset signal triggered on ${BOARD}."
}

reboot_ssh() {
  log_info "Attempting SSH reboot to ${TARGET_USER}@${TARGET_IP:-<not configured>}..."
  if [ -z "$TARGET_IP" ]; then
    log_error "TARGET_IP is not set in tools/deploy/boards/${BOARD}.env"
    return 1
  fi

  local SSH_OPTS=(-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o ConnectTimeout=3)
  if [ -n "$TARGET_PORT" ]; then SSH_OPTS+=(-p "$TARGET_PORT"); fi
  if [ -n "$TARGET_KEY" ] && [ -f "$TARGET_KEY" ]; then SSH_OPTS+=(-i "$TARGET_KEY"); fi

  if [ "$DRY_RUN" = true ]; then
    log_info "[DRY-RUN] Would execute: ssh ${TARGET_USER}@${TARGET_IP} 'reboot'"
    return 0
  fi

  ssh "${SSH_OPTS[@]}" "${TARGET_USER}@${TARGET_IP}" "nohup reboot >/dev/null 2>&1 &" 2>/dev/null || true
  log_success "SSH reboot command sent to ${TARGET_IP}."
}

reboot_sysrq_serial() {
  log_info "Attempting Magic SysRq reset over serial port ${SERIAL_PORT:-<not configured>}..."
  if [ -z "$SERIAL_PORT" ]; then
    log_error "BOARD_SERIAL_PORT is not set."
    return 1
  fi

  if [ "$DRY_RUN" = true ]; then
    log_info "[DRY-RUN] Would send SysRq Break + 'b' to ${SERIAL_PORT}"
    return 0
  fi

  if [ ! -e "$SERIAL_PORT" ]; then
    log_error "Serial port device '$SERIAL_PORT' is invalid or not found."
    return 1
  fi

  python3 - <<EOF
import serial, time
try:
    s = serial.Serial('$SERIAL_PORT', int('$SERIAL_BAUD'), timeout=1)
    s.send_break(duration=0.25)
    time.sleep(0.1)
    s.write(b'b')
    s.close()
    print("  [OK] SysRq Break+b reset sent.")
except Exception as e:
    print(f"  [ERROR] SysRq failed: {e}")
    exit(1)
EOF
  log_success "Magic SysRq reboot triggered."
}

reboot_power_relay() {
  log_info "Attempting Power Cycle Relay reset..."
  if [ -n "${POWER_RELAY_CMD:-}" ]; then
    if [ "$DRY_RUN" = true ]; then
      log_info "[DRY-RUN] Would run: $POWER_RELAY_CMD"
      return 0
    fi
    eval "$POWER_RELAY_CMD"
    log_success "Power relay cycle executed."
  else
    log_warn "POWER_RELAY_CMD not configured in tools/deploy/boards/${BOARD}.env"
  fi
}

# ------------------------------------------------------------------------------
# Dispatch
# ------------------------------------------------------------------------------
case "$METHOD" in
  uboot_serial|serial) reboot_uboot_serial ;;
  ssh)                 reboot_ssh ;;
  sysrq_serial|sysrq)  reboot_sysrq_serial ;;
  power_relay|relay)   reboot_power_relay ;;
  *)
    log_error "Unknown reboot method: $METHOD (supported: uboot_serial, ssh, sysrq_serial, power_relay)"
    exit 1
    ;;
esac
