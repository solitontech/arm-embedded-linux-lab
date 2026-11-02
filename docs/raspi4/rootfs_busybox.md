# Raspberry Pi 4: Building a Minimal BusyBox Root Filesystem

You need a minimal userspace to spawn `/sbin/init` or `/bin/sh`. BusyBox combines tiny versions of common UNIX utilities into a single multi-call binary — recommended for first bringup.

## 1. Configure & Build BusyBox

BusyBox is included as a Git submodule at `shared/rootfs/busybox`. No need to clone separately.

```bash
cd /workspace/shared/rootfs/busybox
make defconfig
```

Configure static linking so BusyBox has no dynamic shared library dependencies:
```bash
# Enable static build
sed -i 's/# CONFIG_STATIC is not set/CONFIG_STATIC=y/' .config

make -j$(nproc) ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- install CONFIG_PREFIX=/tmp/rpi-rootfs
```

## 2. Create the Standard Linux Directory Hierarchy
```bash
cd /tmp/rpi-rootfs
sudo mkdir -p dev proc sys etc root home tmp var/log etc/init.d
sudo chmod 1777 tmp
```

## 3. Create Essential Device Nodes
When the kernel boots without devtmpfs mounted, it requires `/dev/console` and `/dev/null`:
```bash
sudo mknod -m 600 /tmp/rpi-rootfs/dev/console c 5 1
sudo mknod -m 666 /tmp/rpi-rootfs/dev/null c 1 3
```

## 4. Configure `/etc/inittab`
Create `/tmp/rpi-rootfs/etc/inittab`:
```ini
# /etc/inittab - Minimal BusyBox init configuration
::sysinit:/etc/init.d/rcS
::askfirst:-/bin/sh
::restart:/sbin/init
::ctrlaltdel:/sbin/reboot
::shutdown:/bin/umount -a -r
```

## 5. Create `/etc/init.d/rcS` (Startup Script)
Create `/tmp/rpi-rootfs/etc/init.d/rcS`:
```bash
#!/bin/sh
# /etc/init.d/rcS - System startup script

# Mount pseudo filesystems
mount -t proc proc /proc
mount -t sysfs sysfs /sys
mount -t devtmpfs devtmpfs /dev
mkdir -p /dev/pts
mount -t devpts devpts /dev/pts

echo "=========================================================="
echo " Welcome to Soliton ARM Embedded Linux Lab — Pi 4 Bringup"
echo " Kernel: $(uname -r) on $(uname -m)"
echo "=========================================================="
```
Make the startup script executable:
```bash
sudo chmod +x /tmp/rpi-rootfs/etc/init.d/rcS
```

---

## 6. Adding SSH Access (Dropbear)

The base BusyBox rootfs only provides a serial console. To enable remote access via `./lab ssh --board=rpi4`, cross-compile **Dropbear** — a lightweight SSH server designed for embedded systems.

### 6.1 Install Cross-Architecture Dependencies

Dropbear needs `crypt()` for password authentication. Install the AArch64 `libcrypt-dev` inside the Docker container:

```bash
# Inside Docker container (as root / with sudo)
sudo dpkg --add-architecture arm64
echo "deb [arch=arm64] http://ports.ubuntu.com/ubuntu-ports jammy main universe" \
    | sudo tee /etc/apt/sources.list.d/arm64-ports.list
echo "deb [arch=arm64] http://ports.ubuntu.com/ubuntu-ports jammy-updates main universe" \
    | sudo tee -a /etc/apt/sources.list.d/arm64-ports.list
sudo apt-get update
sudo apt-get install -y libcrypt-dev:arm64 autoconf
```

### 6.2 Cross-Compile Dropbear

```bash
# Inside Docker container
cd /tmp
git clone --depth=1 --branch DROPBEAR_2024.86 https://github.com/mkj/dropbear.git
cd dropbear

# Generate configure script from autoconf
autoconf && autoheader

# Configure for AArch64 static build (no shared lib deps on target)
ROOTFS=/workspace/nfs/rpi4-rootfs
./configure --host=aarch64-linux-gnu \
    --prefix=${ROOTFS} \
    --disable-zlib \
    --enable-static \
    CC=aarch64-linux-gnu-gcc \
    LDFLAGS="-static"

make -j$(nproc) PROGRAMS="dropbear dropbearkey dbclient scp"
make install PROGRAMS="dropbear dropbearkey dbclient scp"
```

This installs:
- `sbin/dropbear` — SSH daemon
- `bin/dropbearkey` — Host key generator
- `bin/dbclient` — SSH client
- `bin/scp` — Secure copy

> [!TIP]
> Remove the installed manpages to save space: `sudo rm -rf ${ROOTFS}/share`

### 6.3 Create Required Directories & Config

```bash
ROOTFS=/workspace/nfs/rpi4-rootfs

# Dropbear host key directory (keys are generated at first boot by rcS)
mkdir -p ${ROOTFS}/etc/dropbear

# Password and shadow files (root with no password — lab use only)
tee ${ROOTFS}/etc/passwd > /dev/null <<'EOF'
root::0:0:root:/root:/bin/sh
EOF

tee ${ROOTFS}/etc/group > /dev/null <<'EOF'
root:x:0:
EOF

# /etc/shells (required by some SSH implementations)
tee ${ROOTFS}/etc/shells > /dev/null <<'EOF'
/bin/sh
EOF
```

> [!CAUTION]
> This configures root with **no password** — suitable for an isolated lab network only. For any network-exposed setup, set a password with `chpasswd` after first boot or use key-only authentication.

### 6.4 Update `rcS` to Start Networking & Dropbear

The committed `nfs/rpi4-rootfs/etc/init.d/rcS` already handles Dropbear startup. The key additions over the base script from step 5 are:

- **Network fallback**: The kernel `ip=` boot parameter configures eth0 during NFS mount. `rcS` detects this and only runs `ifconfig` as a fallback if eth0 has no IP.
- **Host key generation**: On first boot, ed25519 and RSA host keys are generated and persisted on the NFS rootfs.
- **Dropbear daemon**: Started with `-R` (generate missing keys) and `-B` (allow blank passwords for the lab's passwordless root).
- **Console detection**: Parses `console=` from `/proc/cmdline` so output goes to the correct serial device.

See the committed [rcS](../../nfs/rpi4-rootfs/etc/init.d/rcS) for the full script.

### 6.5 Verify SSH

After booting the Pi, from inside the Docker container or host:
```bash
./lab ssh --board=rpi4
# or directly:
ssh -o StrictHostKeyChecking=no root@192.168.1.150
```

The boot banner on the serial console will show the SSH address:
```text
==========================================================
 Welcome to Soliton ARM Embedded Linux Lab
 Kernel: 6.6.y on aarch64
 SSH:    root@192.168.1.150:22
==========================================================
```

---

## 7. NTP Time Synchronization (BusyBox `ntpd`)

The Raspberry Pi 4 has **no hardware Real-Time Clock (RTC)**. On every boot, the system clock starts at the Unix Epoch (`1970-01-01 00:00:00 UTC`) and only advances by uptime — so all log timestamps, TLS certificates, and make dependency checks are wrong until the clock is synchronized.

### Why This Matters

| Symptom | Root Cause |
|---|---|
| Log timestamps show `1970-01-01` | No RTC, clock not yet synced |
| `make` always rebuilds targets | File mtimes in the future (2026) vs. system 1970 |
| TLS handshakes fail | Certificate validity window mismatch |

### How BusyBox `ntpd` Works Here

BusyBox ships `ntpd` as part of its single multi-call binary (enabled by default in `defconfig`). The key flags used in `rcS`:

| Flag | Meaning |
|---|---|
| `-q` | **One-shot / quit** — sync once, then exit (don't stay as a background daemon) |
| `-n` | **Foreground** — don't fork (needed so `rcS` can wait for it to finish) |
| `-p <server>` | NTP peer to query |

> [!NOTE]
> `ntpd -q -n` blocks until at least one response is received or it times out (~15 s).
> If the board has no internet route, the sync simply fails gracefully and boot continues.

### `rcS` Integration

The following block is already present in [`nfs/rpi4-rootfs/etc/init.d/rcS`](../../nfs/rpi4-rootfs/etc/init.d/rcS) (inserted after networking is confirmed, before Dropbear starts):

```sh
# --- NTP time sync ---
# The RPi4 has no hardware RTC; clock defaults to 1970-01-01 until synced.
# Run ntpd in one-shot mode (-q) to set the clock before anything else logs.
printf '[init] Syncing time via NTP...\r\n'
ntpd -q -n -p pool.ntp.org 2>/dev/null && \
    printf '[init] Time synced: %s\r\n' "$(date)" || \
    printf '[init] NTP sync failed (no internet?). Current time: %s\r\n' "$(date)"
```

### Verifying on the Target

SSH into the Pi and confirm the clock is correct:

```bash
# SSH into the Pi
./lab ssh --board=rpi4

# Check current time
date

# Run a manual one-shot sync (useful for debugging)
ntpd -q -n -p pool.ntp.org
date
```

Expected boot console output (on the serial/SSH terminal):
```text
[init] Syncing time via NTP...
[init] Time synced: Wed Oct 21 09:05:42 UTC 2026
```

> [!TIP]
> If sync fails (e.g., the lab network has no internet gateway), you can manually set the clock via SSH:
> ```bash
> date -s "2026-10-21 09:00:00"
> ```
> Or add a gateway to the `rcS` networking fallback block to restore internet access.

### Using a Local NTP Server

If your lab network has a local NTP server (e.g., a router at `192.168.1.1`), point `ntpd` at it instead to avoid relying on internet access:

```sh
ntpd -q -n -p 192.168.1.1 2>/dev/null
```

Update the `-p` argument in `nfs/rpi4-rootfs/etc/init.d/rcS` accordingly.

---

**Previous:** [Kernel Cross-Compilation](kernel_build.md) | **Next:** [U-Boot, TFTP & NFS Boot](uboot_tftp_boot.md)
