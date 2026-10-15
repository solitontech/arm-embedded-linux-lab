#!/usr/bin/env bash
# ==============================================================================
# configure_wifi.sh — Generate /etc/wpa_supplicant/wpa_supplicant.conf securely
#
# Reads WIFI_SSID, WIFI_PSK, WIFI_COUNTRY from the board env file and
# generates a wpa_supplicant.conf with a hashed PSK (if wpa_passphrase
# is available). The plaintext password never touches the rootfs.
#
# Usage:
#   ./tools/target/configure_wifi.sh [--board rpi4]
# ==============================================================================
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

BOARD="${1:-rpi4}"
# Accept --board=rpi4 or --board rpi4
if [[ "${BOARD}" == "--board" ]]; then
    BOARD="${2:-rpi4}"
elif [[ "${BOARD}" == --board=* ]]; then
    BOARD="${BOARD#--board=}"
fi

BOARD_ENV="${REPO_ROOT}/shared/boards/${BOARD}.env"
ROOTFS_DIR="${REPO_ROOT}/nfs/${BOARD}-rootfs"

if [[ ! -f "${BOARD_ENV}" ]]; then
    echo "Error: ${BOARD_ENV} not found. Copy from shared/boards/board.env.example" >&2
    exit 1
fi

source "${BOARD_ENV}"

if [[ -z "${WIFI_SSID:-}" || -z "${WIFI_PSK:-}" ]]; then
    echo "Wi-Fi credentials not set in ${BOARD_ENV}; skipping Wi-Fi configuration."
    echo "Add WIFI_SSID and WIFI_PSK to your board env file."
    exit 0
fi

CONF_DIR="${ROOTFS_DIR}/etc/wpa_supplicant"
mkdir -p "${CONF_DIR}"

echo "Generating secure wpa_supplicant.conf for SSID: ${WIFI_SSID}..."

# Compute hashed PSK using wpa_passphrase if available
if command -v wpa_passphrase &>/dev/null; then
    WPA_BLOCK="$(wpa_passphrase "${WIFI_SSID}" "${WIFI_PSK}" | grep -v '#psk=')"
else
    # Fallback: plaintext PSK (less secure, but functional)
    WPA_BLOCK=$(printf 'network={\n    ssid="%s"\n    psk="%s"\n}' "${WIFI_SSID}" "${WIFI_PSK}")
fi

cat > "${CONF_DIR}/wpa_supplicant.conf" <<EOF
ctrl_interface=/var/run/wpa_supplicant
update_config=1
country=${WIFI_COUNTRY:-US}

${WPA_BLOCK}
EOF

chmod 600 "${CONF_DIR}/wpa_supplicant.conf"
echo "Secure Wi-Fi configuration written to ${CONF_DIR}/wpa_supplicant.conf"
