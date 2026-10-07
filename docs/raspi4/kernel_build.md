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

## 5. Deploy Kernel Artifacts

After building, you have two deployment paths depending on your boot method:

**TFTP boot (recommended for development):** Copy to the Docker TFTP directory — the Pi fetches them over the network on every boot:
```bash
cp arch/arm64/boot/Image /workspace/tftp/Image
cp arch/arm64/boot/dts/broadcom/bcm2711-rpi-4-b.dtb /workspace/tftp/bcm2711-rpi-4-b.dtb
```

**Direct SD card boot (first-time bringup only):** The deploy script handles copying firmware, U-Boot, config, and boot script to the SD card automatically:
```bash
cd /workspace/shared/boot
make deploy-sd BOARD=rpi4
```

See [U-Boot, TFTP & NFS Boot](uboot_tftp_boot.md) for the full TFTP workflow.

## 6. Install Kernel Modules to `ROOTFS` Partition
```bash
sudo make modules_install INSTALL_MOD_PATH=/tmp/rpi-rootfs
```
This installs kernel drivers into `/tmp/rpi-rootfs/lib/modules/<kernel-version>/`.

---

**Previous:** [SD Card Setup](sd_card_setup.md) | **Next:** [BusyBox Root Filesystem](rootfs_busybox.md)
