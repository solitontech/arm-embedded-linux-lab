#!/usr/bin/env bash
set -e

# ==============================================================================
# ARM Embedded Linux Lab — Container Entrypoint
# Configures and starts persistent TFTP daemon pointing to /workspace/tftp,
# sets readable permissions, and switches to labuser.
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
chmod -R 777 "${TFTP_DIR}" 2>/dev/null || chmod -R a+rX "${TFTP_DIR}" 2>/dev/null || true

# 5. Start or restart tftpd-hpa service
if command -v service &>/dev/null; then
    service tftpd-hpa restart &>/dev/null || /usr/sbin/in.tftpd --listen --user tftp --address :69 --secure "${TFTP_DIR}" &>/dev/null || true
else
    /usr/sbin/in.tftpd --listen --user tftp --address :69 --secure "${TFTP_DIR}" &>/dev/null || true
fi

# 6. Execute main command as labuser (UID 1000)
if [ "$(id -u)" -eq 0 ]; then
    exec sudo -E -u labuser "$@"
else
    exec "$@"
fi
