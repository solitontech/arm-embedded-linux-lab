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

### 6.1 Cross-Compile Dropbear

```bash
# Inside Docker container
cd /workspace
git clone --depth=1 --branch DROPBEAR_2024.86 https://github.com/mkj/dropbear.git
cd dropbear

# Configure for AArch64 static build (no shared lib deps on target)
./configure --host=aarch64-linux-gnu \
    --prefix=/tmp/rpi-rootfs \
    --disable-zlib \
    --enable-static \
    CC=aarch64-linux-gnu-gcc \
    LDFLAGS="-static"

make -j$(nproc) PROGRAMS="dropbear dropbearkey dbclient scp"
make install
```

This installs:
- `/tmp/rpi-rootfs/sbin/dropbear` — SSH daemon
- `/tmp/rpi-rootfs/bin/dropbearkey` — Host key generator
- `/tmp/rpi-rootfs/bin/dbclient` — SSH client
- `/tmp/rpi-rootfs/bin/scp` — Secure copy

### 6.2 Create Required Directories & Config

```bash
ROOTFS=/tmp/rpi-rootfs

# Dropbear host key directory
sudo mkdir -p ${ROOTFS}/etc/dropbear

# Password and shadow files (root with no password — lab use only)
sudo tee ${ROOTFS}/etc/passwd > /dev/null <<'EOF'
root::0:0:root:/root:/bin/sh
EOF

sudo tee ${ROOTFS}/etc/group > /dev/null <<'EOF'
root:x:0:
EOF

# /etc/shells (required by some SSH implementations)
sudo tee ${ROOTFS}/etc/shells > /dev/null <<'EOF'
/bin/sh
EOF
```

> [!CAUTION]
> This configures root with **no password** — suitable for an isolated lab network only. For any network-exposed setup, set a password with `chpasswd` after first boot or use key-only authentication.

### 6.3 Update `rcS` to Start Networking & Dropbear

Replace the `rcS` script from step 5 with this expanded version:

```bash
#!/bin/sh
# /etc/init.d/rcS - System startup script

# Mount pseudo filesystems
mount -t proc proc /proc
mount -t sysfs sysfs /sys
mount -t devtmpfs devtmpfs /dev
mkdir -p /dev/pts
mount -t devpts devpts /dev/pts

# Configure network (static IP matching shared/boards/rpi4.env)
ifconfig eth0 192.168.1.150 netmask 255.255.255.0 up
route add default gw 192.168.1.1

# Generate host keys on first boot (persisted on SD/NFS rootfs)
if [ ! -f /etc/dropbear/dropbear_rsa_host_key ]; then
    echo "[init] Generating Dropbear host keys..."
    dropbearkey -t rsa -f /etc/dropbear/dropbear_rsa_host_key
    dropbearkey -t ecdsa -f /etc/dropbear/dropbear_ecdsa_host_key
fi

# Start SSH daemon
dropbear -R -B

echo "=========================================================="
echo " Soliton ARM Embedded Linux Lab — Pi 4 Bringup"
echo " Kernel: $(uname -r) on $(uname -m)"
echo " SSH:    root@$(ifconfig eth0 | grep 'inet ' | awk '{print $2}'):22"
echo "=========================================================="
```

### 6.4 Verify SSH

After booting, from your host:
```bash
./lab ssh --board=rpi4
# or directly:
ssh root@192.168.1.150
```

---

**Previous:** [Kernel Cross-Compilation](kernel_build.md) | **Next:** [U-Boot, TFTP & NFS Boot](uboot_tftp_boot.md)
