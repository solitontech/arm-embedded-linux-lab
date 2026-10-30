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

# Static IP configuration — must match cmdline.txt and shared/boards/rpi4.env
setenv ipaddr    192.168.1.150
# Host machine LAN IP (confirmed: enp2s0 on 192.168.0.0/23)
setenv serverip  192.168.1.220

echo "==> Soliton ARM Embedded Linux Lab"
echo "==> Board IP : ${ipaddr}"
echo "==> Server IP: ${serverip}"

echo "==> Fetching kernel Image via TFTP..."
tftp 0x02000000 Image

# Use the DTB provided by the GPU firmware (at ${fdt_addr}) instead of loading
# a fresh one via TFTP. The GPU applies dtoverlay= entries from config.txt
# (e.g. imx219 camera) to the DTB before passing it to U-Boot. Loading a
# separate DTB via TFTP would discard those overlays.
echo "==> Using GPU-provided DTB at ${fdt_addr} (overlays preserved)"

setenv bootargs "console=ttyS0,115200 console=tty1 root=/dev/nfs rw rootwait nfsroot=192.168.1.220:/workspace/nfs/rpi4-rootfs,tcp,v3 ip=192.168.1.150:::255.255.255.0:rpi4:eth0:off earlycon=bcm2835aux,0xfe215040"

echo "==> Booting Linux kernel..."
booti 0x02000000 - ${fdt_addr}
