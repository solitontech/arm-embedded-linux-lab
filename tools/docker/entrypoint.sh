#!/usr/bin/env bash
set -e

# ==============================================================================
# ARM Embedded Linux Lab — Container Entrypoint
# Configures and starts persistent TFTP daemon pointing to /workspace/tftp,
# sets readable permissions, and switches to labuser.
# On macOS hosts, also bridges socat TCP serial proxies to /dev/ttyVUSB<N>.
# ==============================================================================

TFTP_DIR="/workspace/tftp"

# 1. Ensure /etc/default/tftpd-hpa is configured for /workspace/tftp
cat << 'EOF' > /etc/default/tftpd-hpa
TFTP_USERNAME="tftp"
TFTP_DIRECTORY="/workspace/tftp"
TFTP_ADDRESS=":69"
TFTP_OPTIONS="--secure"
EOF

# 2. Ensure /workspace/tftp exists
mkdir -p "${TFTP_DIR}"

# 3. Ensure test.txt exists for verification if directory is empty
if [ ! -f "${TFTP_DIR}/test.txt" ]; then
    echo "TFTP TEST" > "${TFTP_DIR}/test.txt"
fi

# 4. Ensure tftp daemon user can read/write files inside /workspace/tftp
chmod -R a+rwX "${TFTP_DIR}" 2>/dev/null || true

# 5. Start or restart tftpd-hpa service
if command -v service &>/dev/null; then
    service tftpd-hpa restart &>/dev/null || /usr/sbin/in.tftpd --listen --user tftp --address :69 --secure "${TFTP_DIR}" &>/dev/null || true
else
    /usr/sbin/in.tftpd --listen --user tftp --address :69 --secure "${TFTP_DIR}" &>/dev/null || true
fi

# 6. macOS serial bridge — create PTY devices from host socat TCP proxies.
#    run.sh sets SERIAL_PROXY_PORTS="54320:/dev/cu.usbserial-XXXX,54321:..."
#    Each entry creates /dev/ttyVUSB<N> backed by a socat TCP connection.
if [[ -n "${SERIAL_PROXY_PORTS:-}" ]]; then
    _host="host.docker.internal"
    if ! getent hosts "${_host}" &>/dev/null; then
        _host="127.0.0.1"
    fi
    idx=0
    IFS=',' read -ra _entries <<< "${SERIAL_PROXY_PORTS}"
    for _entry in "${_entries[@]}"; do
        _port="${_entry%%:*}"
        _origdev="${_entry##*:}"
        _pty="/dev/ttyVUSB${idx}"
        _compat="/dev/ttyUSB${idx}"
        echo "❯ [SERIAL] Bridging host ${_origdev} → ${_pty} (via TCP ${_host}:${_port})"
        # Run socat in a background respawn loop so connection auto-reconnects
        (
            while true; do
                socat PTY,link="${_pty}",raw,echo=0,mode=666 \
                      TCP:"${_host}":"${_port}" &>/dev/null || true
                sleep 1
            done
        ) &
        # Provide /dev/ttyUSB<N> symlink for out-of-the-box board config compatibility
        (
            for _ in {1..20}; do
                if [[ -e "${_pty}" ]]; then
                    [[ ! -e "${_compat}" ]] && ln -sf "${_pty}" "${_compat}"
                    break
                fi
                sleep 0.2
            done
        ) &
        idx=$(( idx + 1 ))
    done
    sleep 0.8
fi

# 7. Execute main command as labuser (UID 1000)
if [ "$(id -u)" -eq 0 ]; then
    export HOME="/home/labuser"
    exec sudo -E -u labuser HOME=/home/labuser "$@"
else
    exec "$@"
fi
