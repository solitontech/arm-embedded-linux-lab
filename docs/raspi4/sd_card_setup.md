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

## 2. Populating the BOOT Partition

The monorepo already has all the boot artifacts committed in [`shared/bsp/rpi4/`](../../shared/bsp/rpi4/) — firmware blobs, `config.txt`, `cmdline.txt`, U-Boot binary, and boot script. The deploy script copies them automatically:

```bash
cd shared/boot
make deploy-sd BOARD=rpi4
```

This runs [`tools/target/deploy_bootfs.sh`](../../tools/target/deploy_bootfs.sh), which detects the mounted SD card (macOS/Linux), cleans the BOOT partition, compiles `boot.cmd` → `boot.scr`, and copies all required files.

> [!NOTE]
> If you need to re-fetch firmware from upstream (e.g. after a Pi firmware update):
> ```bash
> cd shared/boot
> make fetch-firmware BOARD=rpi4
> ```

### Understanding the Boot Configuration

The following files in `shared/bsp/rpi4/` control the boot process. Edit them in the repo, then re-run `make deploy-sd` to apply.

**`config.txt`** — GPU firmware configuration:

| Setting | Purpose |
|:---|:---|
| `arm_64bit=1` | Force AArch64 execution mode |
| `enable_uart=1` | Enable serial UART console |
| `kernel=u-boot.bin` | Load U-Boot as the bootloader |
| `device_tree=bcm2711-rpi-4-b.dtb` | Hardware device tree |
| `gpu_mem=128` | Minimal GPU memory for headless operation |

**`cmdline.txt`** — Kernel boot parameters (passed via the `chosen/bootargs` Device Tree node):

> [!IMPORTANT]
> `cmdline.txt` **MUST be a single continuous line** with no newline/carriage return character at the end.

| Parameter | Purpose |
|:---|:---|
| `console=serial0,115200` | Direct `printk` and getty to the physical UART |
| `console=tty1` | Duplicate output to HDMI terminal |
| `root=/dev/mmcblk0p2` | Mount SD card partition 2 as rootfs |
| `rw` | Mount root read-write |
| `rootwait` | Wait for the SD/MMC driver to finish probing |
| `rootfstype=ext4` | Mount directly as ext4 |
| `earlycon` | Enable early printk before full TTY driver init |

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
