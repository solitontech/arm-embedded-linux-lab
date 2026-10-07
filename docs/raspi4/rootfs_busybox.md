# Raspberry Pi 4: Building a Minimal BusyBox Root Filesystem

You need a minimal userspace to spawn `/sbin/init` or `/bin/sh`. BusyBox combines tiny versions of common UNIX utilities into a single multi-call binary — recommended for first bringup.

## 1. Download & Build BusyBox
```bash
cd /workspace
git clone --depth=1 --branch 1_36_stable https://github.com/mirror/busybox.git
cd busybox

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

**Previous:** [Kernel Cross-Compilation](kernel_build.md) | **Next:** [U-Boot, TFTP & NFS Boot](uboot_tftp_boot.md)
