#!/usr/bin/env bash
# ==============================================================================
# tools/eeprom/prepare_netboot.sh
#
# Prepares RPi4 EEPROM recovery files for network boot — no RPi OS required.
#
# What it does:
#   1. Downloads the official EEPROM firmware + recovery.bin from GitHub
#   2. Downloads the rpi-eeprom-config tool (Python, runs on any OS)
#   3. Patches the EEPROM binary with netboot config (BOOT_ORDER, TFTP_PREFIX)
#   4. Outputs recovery.bin + pieeprom.upd ready to copy to the SD boot partition
#
# Usage:
#   ./tools/eeprom/prepare_netboot.sh [--output-dir DIR]
#
# After running, copy the output files to the SD card boot partition:
#   cp <output-dir>/recovery.bin <output-dir>/pieeprom.upd /media/$USER/bootfs/
#
# Then power on the Pi — the GPU will flash the EEPROM and reboot.
# ==============================================================================
set -euo pipefail

# ── Configuration ────────────────────────────────────────────────────────────
EEPROM_CHANNEL="default"
EEPROM_REPO="https://github.com/raspberrypi/rpi-eeprom"
EEPROM_RAW="https://raw.githubusercontent.com/raspberrypi/rpi-eeprom/master/firmware-2711/${EEPROM_CHANNEL}"
EEPROM_API="https://api.github.com/repos/raspberrypi/rpi-eeprom/contents/firmware-2711/${EEPROM_CHANNEL}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUTPUT_DIR="${1:-${SCRIPT_DIR}/output}"

# ── Colour helpers ───────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; CYAN='\033[0;36m'; BOLD='\033[1m'; RESET='\033[0m'
info()  { echo -e "${BOLD}${CYAN}❯${RESET} $*"; }
ok()    { echo -e "${BOLD}${GREEN}✔${RESET} $*"; }
err()   { echo -e "${BOLD}${RED}✖ ERROR:${RESET} $*" >&2; exit 1; }

# ── Preflight checks ────────────────────────────────────────────────────────
command -v python3 &>/dev/null || err "python3 is required but not found"
command -v curl    &>/dev/null || command -v wget &>/dev/null || err "curl or wget required"

fetch() {
    local url="$1" dest="$2"
    if command -v curl &>/dev/null; then
        curl -fSL --retry 3 -o "$dest" "$url"
    else
        wget -q -O "$dest" "$url"
    fi
}

mkdir -p "${OUTPUT_DIR}"

# ── Step 1: Auto-detect latest EEPROM firmware ───────────────────────────────
# Query the GitHub API to find the newest pieeprom-*.bin in the channel.
info "Querying latest ${EEPROM_CHANNEL} EEPROM firmware from GitHub..."
PIEEPROM_BIN=$(curl -fsSL "${EEPROM_API}" | python3 -c "
import json, sys
files = [f['name'] for f in json.load(sys.stdin)
         if f['name'].startswith('pieeprom-') and f['name'].endswith('.bin')]
files.sort()
print(files[-1])
" 2>/dev/null) || err "Failed to query GitHub API for firmware list"
ok "Latest firmware: ${PIEEPROM_BIN}"

# ── Step 2: Download EEPROM firmware binary ──────────────────────────────────
if [[ -f "${OUTPUT_DIR}/${PIEEPROM_BIN}" ]]; then
    ok "EEPROM firmware already downloaded: ${PIEEPROM_BIN}"
else
    info "Downloading EEPROM firmware: ${PIEEPROM_BIN}"
    fetch "${EEPROM_RAW}/${PIEEPROM_BIN}" "${OUTPUT_DIR}/${PIEEPROM_BIN}"
    ok "Downloaded ${PIEEPROM_BIN}"
fi

# ── Step 3: Download recovery.bin ────────────────────────────────────────────
if [[ -f "${OUTPUT_DIR}/recovery.bin" ]]; then
    ok "recovery.bin already present"
else
    info "Downloading recovery.bin"
    fetch "${EEPROM_RAW}/recovery.bin" "${OUTPUT_DIR}/recovery.bin"
    ok "Downloaded recovery.bin"
fi

# ── Step 4: Obtain rpi-eeprom-config (standalone Python script) ──────────────
RPI_EEPROM_CONFIG="${OUTPUT_DIR}/rpi-eeprom-config"
if [[ -f "${RPI_EEPROM_CONFIG}" ]]; then
    ok "rpi-eeprom-config already present"
else
    info "Obtaining rpi-eeprom-config tool"
    # Try direct download first; fall back to sparse git clone if rate-limited
    if ! fetch "https://raw.githubusercontent.com/raspberrypi/rpi-eeprom/master/rpi-eeprom-config" \
               "${RPI_EEPROM_CONFIG}" 2>/dev/null; then
        info "Direct download failed (rate limit?), using sparse git clone..."
        _tmp="$(mktemp -d)"
        GIT_SSL_NO_VERIFY=1 git clone --depth=1 --filter=blob:none --sparse \
            "${EEPROM_REPO}.git" "${_tmp}/rpi-eeprom" 2>/dev/null
        (cd "${_tmp}/rpi-eeprom" && git sparse-checkout set --skip-checks rpi-eeprom-config 2>/dev/null)
        cp "${_tmp}/rpi-eeprom/rpi-eeprom-config" "${RPI_EEPROM_CONFIG}"
        rm -rf "${_tmp}"
    fi
    chmod +x "${RPI_EEPROM_CONFIG}"
    ok "Obtained rpi-eeprom-config"
fi

# ── Step 5: Create netboot config ────────────────────────────────────────────
BOOT_CONF="${OUTPUT_DIR}/boot.conf"
cat > "${BOOT_CONF}" <<'CONF'
[all]
BOOT_UART=1

# Network first (0x2), then SD fallback (0x1); 0xf restarts the sequence
BOOT_ORDER=0xf21

# Timeout before trying next boot mode (units of 100ms)
BOOT_ORDER_TIMEOUT=5

# Flat TFTP directory — do not prepend the Pi serial number to requests
TFTP_PREFIX=0

# Allow network boot without any SD/USB media present
NETWORK_INSTALL_ENABLED=1
CONF
ok "Created netboot config: ${BOOT_CONF}"

# ── Step 6: Patch config into EEPROM binary ──────────────────────────────────
info "Patching EEPROM binary with netboot config..."
python3 "${RPI_EEPROM_CONFIG}" \
    --config "${BOOT_CONF}" \
    --out "${OUTPUT_DIR}/pieeprom.upd" \
    "${OUTPUT_DIR}/${PIEEPROM_BIN}"
ok "Created patched EEPROM: ${OUTPUT_DIR}/pieeprom.upd"

# ── Step 7: Verify ──────────────────────────────────────────────────────────
info "Verifying patched config:"
python3 "${RPI_EEPROM_CONFIG}" "${OUTPUT_DIR}/pieeprom.upd"

# ── Done ─────────────────────────────────────────────────────────────────────
echo ""
echo -e "${BOLD}${GREEN}═══════════════════════════════════════════════════════════${RESET}"
echo -e "${BOLD}${GREEN} EEPROM netboot files ready!${RESET}"
echo -e "${BOLD}${GREEN}═══════════════════════════════════════════════════════════${RESET}"
echo ""
echo "  Files:"
echo "    ${OUTPUT_DIR}/recovery.bin"
echo "    ${OUTPUT_DIR}/pieeprom.upd"
echo ""
echo "  Next steps:"
echo "    1. Mount the SD card boot partition"
echo "    2. Copy the files:"
echo "       cp ${OUTPUT_DIR}/recovery.bin ${OUTPUT_DIR}/pieeprom.upd /media/\$USER/bootfs/"
echo "    3. Insert SD card into the Pi and power on"
echo "    4. Wait for the green LED to flash rapidly (EEPROM is being written)"
echo "    5. The Pi reboots automatically — remove the SD card"
echo "    6. On next power-on, the Pi will network-boot via TFTP"
echo ""
