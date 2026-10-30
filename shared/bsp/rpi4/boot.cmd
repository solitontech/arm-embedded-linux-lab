# ==============================================================================
# boot.cmd — RPi4 U-Boot Boot Script (Dev/Prod auto-detect)
#
# Boot modes (auto-detected):
#   PRODUCTION  — SD card has partition 2: kernel + rootfs from SD, no network
#   DEVELOPMENT — no partition 2: kernel via TFTP, rootfs via NFS from Docker
#
# HOW TO COMPILE (inside Docker container):
#   mkimage -C none -A arm64 -T script -d shared/bsp/rpi4/boot.cmd shared/bsp/rpi4/boot.scr
#
# HOW TO DEPLOY:
#   make -C shared/boot deploy-sd BOARD=rpi4          (dev — BOOT partition only)
#   make -C shared/boot deploy-sd BOARD=rpi4 MODE=prod (prod — BOOT + SquashFS)
# ==============================================================================

setenv console "console=ttyS0,115200 console=tty1 earlycon=bcm2835aux,0xfe215040"

echo "==> Soliton ARM Embedded Linux Lab"

# Use the DTB provided by the GPU firmware (at ${fdt_addr}) instead of loading
# a fresh one via TFTP. The GPU applies dtoverlay= entries from config.txt
# (e.g. imx219 camera) to the DTB before passing it to U-Boot. Loading a
# separate DTB via TFTP would discard those overlays.
echo "==> Using GPU-provided DTB at ${fdt_addr} (overlays preserved)"

# Auto-detect boot mode: partition 2 on SD → production, otherwise → dev
if mmc dev 0 && mmc rescan && part number mmc 0 2 partnum; then
    echo "==> PRODUCTION: kernel + SquashFS from SD card"
    load mmc 0:1 0x02000000 Image
    setenv bootargs "${console} root=/dev/mmcblk0p2 rootfstype=squashfs ro rootwait"
else
    # Network boot — need IP configuration for TFTP + NFS
    setenv ipaddr    192.168.1.150
    setenv serverip  192.168.1.220
    echo "==> DEVELOPMENT: TFTP kernel + NFS rootfs from ${serverip}"
    tftp 0x02000000 Image
    setenv bootargs "${console} root=/dev/nfs rw rootwait nfsroot=${serverip}:/workspace/nfs/rpi4-rootfs,tcp,v3 ip=${ipaddr}:::255.255.255.0:rpi4:eth0:off"
fi

echo "==> Booting Linux kernel..."
booti 0x02000000 - ${fdt_addr}
