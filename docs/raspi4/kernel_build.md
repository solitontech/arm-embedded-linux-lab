# Raspberry Pi 4: Cross-Compiling the Linux Kernel & Device Tree (AArch64)

You can perform this step directly inside the monorepo Docker container (`./lab docker`) or on your host.

## 1. Environment Setup
```bash
# Toolchain prefix (installed in Docker / Ubuntu: gcc-aarch64-linux-gnu)
export ARCH=arm64
export CROSS_COMPILE=aarch64-linux-gnu-
```

## 2. Clone the Raspberry Pi Kernel Source
We target the long-term stable `rpi-6.6.y` branch:
```bash
cd /workspace # or your preferred scratch directory
git clone --depth=1 --branch rpi-6.6.y https://github.com/raspberrypi/linux.git rpi-linux
cd rpi-linux
```

## 3. Configure the Kernel
Use the Broadcom 2711 64-bit default configuration:
```bash
make bcm2711_defconfig
```

### Optional: Verify Critical Built-in Drivers (`make menuconfig`)
For a clean manual bringup, the following must be compiled **statically into the kernel (`=y`)**, NOT as loadable modules (`=m`), otherwise the kernel cannot read `/dev/mmcblk0p2` to mount root:
* `CONFIG_MMC=y`
* `CONFIG_MMC_BCM2835=y`
* `CONFIG_MMC_SDHCI_IPROC=y`
* `CONFIG_EXT4_FS=y`
* `CONFIG_SERIAL_8250=y`
* `CONFIG_SERIAL_AMBA_PL011=y`
* `CONFIG_SERIAL_AMBA_PL011_CONSOLE=y`

## 4. Compile Kernel, Modules & Device Tree
```bash
# Build using all CPU cores
make -j$(nproc) Image modules dtbs
```

## 5. Copy Kernel & DTB to `BOOT` Partition
```bash
# 1. Uncompressed 64-bit kernel image
sudo cp arch/arm64/boot/Image /tmp/rpi-boot/Image

# 2. Raspberry Pi 4 Model B Device Tree Blob
sudo cp arch/arm64/boot/dts/broadcom/bcm2711-rpi-4-b.dtb /tmp/rpi-boot/bcm2711-rpi-4-b.dtb

# 3. Device Tree Overlays directory
sudo mkdir -p /tmp/rpi-boot/overlays
sudo cp arch/arm64/boot/dts/overlays/*.dtbo /tmp/rpi-boot/overlays/
```

## 6. Install Kernel Modules to `ROOTFS` Partition
```bash
sudo make modules_install INSTALL_MOD_PATH=/tmp/rpi-rootfs
```
This installs kernel drivers into `/tmp/rpi-rootfs/lib/modules/<kernel-version>/`.

---

**Previous:** [SD Card Setup](sd_card_setup.md) | **Next:** [BusyBox Root Filesystem](rootfs_busybox.md)
