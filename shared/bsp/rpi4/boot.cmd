# ==============================================================================
# boot.cmd — RPi4 U-Boot TFTP Boot Script
#
# This script is compiled into boot.scr (via mkimage inside Docker) and placed
# on the SD card BOOT partition. U-Boot auto-executes it on startup.
#
# HOW TO COMPILE (inside Docker container):
#   mkimage -C none -A arm64 -T script -d shared/bsp/rpi4/boot.cmd shared/bsp/rpi4/boot.scr
#
# HOW TO DEPLOY (host machine, SD card mounted):
#   cp shared/bsp/rpi4/boot.scr /media/$USER/BOOT/
# ==============================================================================

# Static IP configuration — must match cmdline.txt and tools/deploy/boards/rpi4.env
setenv ipaddr    192.168.1.150
# Host machine LAN IP (confirmed: enp2s0 on 192.168.0.0/23)
setenv serverip  192.168.1.220

echo "==> ARM Embedded Linux Lab — TFTP Network Boot"
echo "==> Board IP : ${ipaddr}"
echo "==> Server IP: ${serverip}"

echo "==> Fetching kernel Image via TFTP..."
tftp 0x02000000 Image

echo "==> Fetching Device Tree Blob via TFTP..."
tftp 0x06000000 bcm2711-rpi-4-b.dtb

setenv bootargs "console=ttyS0,115200 console=tty1 root=/dev/mmcblk0p2 rw rootwait rootfstype=ext4 earlycon=bcm2835aux,0xfe215040 audit=0 ip=192.168.1.150:::255.255.255.0:rpi4:eth0:off"

echo "==> Booting Linux kernel..."
booti 0x02000000 - 0x06000000
