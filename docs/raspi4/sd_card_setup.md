# Raspberry Pi 4: SD Card Setup & Firmware Configuration

## 1. SD Card Partitioning & Formatting

The Raspberry Pi bootloader requires a specific partition topology:
* **Partition 1 (`BOOT`):** FAT32 (Type `c` or `0x0c` W95 FAT32 LBA), minimum 256MB.
* **Partition 2 (`ROOTFS`):** ext4 (Linux native), taking up the remaining capacity.

### Step 1.1 Identify Your SD Card Device
Insert your SD card into your Linux host / workstation:
```bash
lsblk
# Identify your SD card device node carefully!
# Common nodes: /dev/sdb, /dev/sdc (USB reader) or /dev/mmcblk0 (internal reader)
```
> [!WARNING]
> Ensure you select the correct block device (referred to as `/dev/sdX` below). Writing to the wrong disk will destroy your host data.

### Step 1.2 Partition the Card
```bash
# Wipe previous partition table signatures
sudo wipefs -a /dev/sdX

# Partition with fdisk
sudo fdisk /dev/sdX
```
Inside `fdisk`, enter the following commands:
1. `o` → create a new empty DOS partition table.
2. `n` → new partition → `p` (primary) → `1` → First sector: `2048` → Last sector: `+512M`.
3. `t` → change partition type → `c` (W95 FAT32 LBA).
4. `n` → new partition → `p` (primary) → `2` → default first and last sectors (uses remaining disk).
5. `w` → write changes and exit.

### Step 1.3 Format the Filesystems
```bash
# Force kernel to re-read partition table
sudo partprobe /dev/sdX

# Format Partition 1 as FAT32
sudo mkfs.vfat -F 32 -n "BOOT" /dev/sdX1

# Format Partition 2 as ext4
sudo mkfs.ext4 -F -L "ROOTFS" /dev/sdX2
```

### Step 1.4 Create Mount Directories
```bash
mkdir -p /tmp/rpi-boot
mkdir -p /tmp/rpi-rootfs

sudo mount /dev/sdX1 /tmp/rpi-boot
sudo mount /dev/sdX2 /tmp/rpi-rootfs
```

---

## 2. Obtaining the VideoCore Firmware & Configuration

Raspberry Pi's VideoCore GPU requires proprietary firmware blobs to initialize the SoC memory and clocks before loading Linux.

### Step 2.1 Download Official Firmware Files
Fetch the minimal firmware binaries from the official Raspberry Pi GitHub firmware repository:
```bash
FW_DIR="/tmp/rpi-fw"
mkdir -p "${FW_DIR}"

BASE_URL="https://raw.githubusercontent.com/raspberrypi/firmware/master/boot"

wget -q --show-progress -O "${FW_DIR}/start4.elf" "${BASE_URL}/start4.elf"
wget -q --show-progress -O "${FW_DIR}/fixup4.dat" "${BASE_URL}/fixup4.dat"

# Optional firmware variants (e.g. debug/minimal):
# wget -O "${FW_DIR}/start4cd.elf" "${BASE_URL}/start4cd.elf"
# wget -O "${FW_DIR}/fixup4cd.dat" "${BASE_URL}/fixup4cd.dat"
```

Copy the firmware to the `BOOT` partition:
```bash
sudo cp "${FW_DIR}/start4.elf" /tmp/rpi-boot/
sudo cp "${FW_DIR}/fixup4.dat" /tmp/rpi-boot/
```

### Step 2.2 Create `config.txt`
Create `/tmp/rpi-boot/config.txt` to tell the GPU firmware how to configure clocks, UART, and load the 64-bit ARM Linux kernel:

```ini
# ==============================================================================
# Raspberry Pi 4 Manual 64-Bit Boot Configuration
# ==============================================================================

# Force ARM Cortex-A72 cores into 64-bit execution mode (AArch64)
arm_64bit=1

# Enable primary serial UART console (PL011 / ttyAMA0 on GPIO 14/15)
enable_uart=1
uart_2ndstage=1

# Explicitly specify the Linux kernel and device tree binary
kernel=Image
device_tree=bcm2711-rpi-4-b.dtb

# Allocate minimal memory to VideoCore GPU for headless/inspection operation (128MB)
gpu_mem=128

# Disable rainbow splash screen for faster boot
disable_splash=1

# Disable automatic overlay loading so we control the exact hardware layout
dtoverlay=
```

### Step 2.3 Create `cmdline.txt`
The GPU firmware reads `cmdline.txt` and passes its arguments to the Linux kernel via the `chosen/bootargs` Device Tree node.

> [!IMPORTANT]
> `cmdline.txt` **MUST be a single continuous line** with no newline/carriage return character at the end.

Create `/tmp/rpi-boot/cmdline.txt`:
```text
console=serial0,115200 console=tty1 root=/dev/mmcblk0p2 rw rootwait rootfstype=ext4 earlycon audit=0
```

#### Explanation of Parameters:
* `console=serial0,115200`: Directs `printk` and login getty to the physical UART at 115200 baud.
* `console=tty1`: Also duplicates output to the HDMI virtual terminal if a monitor is attached.
* `root=/dev/mmcblk0p2`: Tells the kernel to mount partition 2 of the SD card as the root filesystem.
* `rw`: Mounts the root filesystem read-write.
* `rootwait`: Forces kernel to pause initialization until the asynchronous SD/MMC card driver finishes probing.
* `rootfstype=ext4`: Avoids probing all filesystem drivers; mounts directly as ext4.
* `earlycon`: Enables early printk logging through the UART before the full TTY driver initializes.

---

## 3. Syncing & Unmounting the SD Card

Before ejecting the card, ensure all write buffers are completely flushed to flash:
```bash
sync

sudo umount /tmp/rpi-boot
sudo umount /tmp/rpi-rootfs

rmdir /tmp/rpi-boot /tmp/rpi-rootfs
```
Now safely unplug the MicroSD card from your workstation.

---

**Previous:** [Boot Architecture](boot_architecture.md) | **Next:** [Kernel Cross-Compilation](kernel_build.md)
