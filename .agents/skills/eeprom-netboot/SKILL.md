---
name: eeprom-netboot
description: Reprogram the RPi4 SPI EEPROM for SD-card-free network boot using the GPU recovery method — no RPi OS required.
---

# EEPROM Network Boot

## Purpose
Configures the Raspberry Pi 4 EEPROM to boot over the network (TFTP) instead of from an SD card. After a one-time flash, the Pi fetches firmware, kernel, and rootfs entirely from the host. This eliminates the SD card from the development loop.

## When to Use This Skill
- Setting up a new RPi4 board for the first time in this lab
- Switching an existing SD-boot board to full network boot
- Recovering an EEPROM with incorrect boot settings
- The user asks about "netboot", "PXE boot", "remove SD card", or "EEPROM config"

## Prerequisites
- Python 3 and `curl` available on the host
- An SD card with a FAT32 boot partition (the existing U-Boot SD card works)
- Physical access to the Pi to insert/remove the SD card
- Docker container running with TFTP and NFS services (see [docker-setup](../docker-setup/SKILL.md))
- TFTP directory populated with firmware (see Step 2 below)

## Instructions

### Step 1: Generate EEPROM Recovery Files
```bash
./tools/eeprom/prepare_netboot.sh
```

The script automatically:
1. Queries GitHub for the latest stable EEPROM firmware (`firmware-2711/default/`)
2. Downloads `recovery.bin` and the firmware binary
3. Downloads `rpi-eeprom-config` (standalone Python tool)
4. Patches the binary with netboot config (`BOOT_ORDER=0xf21`, `TFTP_PREFIX=0`)
5. Outputs `recovery.bin` + `pieeprom.upd` in `tools/eeprom/output/`

### Step 2: Populate the TFTP Directory
```bash
cp shared/bsp/rpi4/start4.elf   tftp/
cp shared/bsp/rpi4/fixup4.dat   tftp/
cp shared/bsp/rpi4/config.txt   tftp/
cp shared/bsp/rpi4/u-boot.bin   tftp/
cp shared/bsp/rpi4/boot.scr     tftp/
cp shared/bsp/rpi4/Image        tftp/
cp shared/bsp/rpi4/bcm2711-rpi-4-b.dtb tftp/
```

### Step 3: Copy Recovery Files to SD Card
```bash
cp tools/eeprom/output/recovery.bin  /media/$USER/bootfs/
cp tools/eeprom/output/pieeprom.upd  /media/$USER/bootfs/
```

### Step 4: Flash the EEPROM
1. Insert the SD card into the Pi and power on.
2. The GPU loads `recovery.bin` instead of `start4.elf`.
3. Green LED flashes rapidly while EEPROM is being written.
4. Pi reboots automatically on success.

### Step 5: Remove SD Card and Verify
1. Power off, remove the SD card permanently.
2. Ensure dnsmasq (DHCP) and the Docker container (TFTP + NFS) are running.
3. Power on — the Pi should network-boot.
4. Verify:
   ```bash
   ./lab console --board=rpi4    # watch serial output
   ./lab ssh --board=rpi4        # verify SSH after boot
   ```

## Key Files
| File | Purpose |
|---|---|
| `tools/eeprom/prepare_netboot.sh` | Generates EEPROM recovery files |
| `tools/eeprom/output/` | Generated files (gitignored) |
| `docs/raspi4/eeprom_netboot.md` | Full documentation with dnsmasq setup, topology, troubleshooting |

## Notes
- The `tools/eeprom/output/` directory is gitignored — generated files are not committed.
- The EEPROM config sets `TFTP_PREFIX=0` so the Pi requests files from a flat directory (e.g., `start4.elf`, not `<serial>/start4.elf`).
- dnsmasq provides DHCP only (no TFTP) — the Docker container's tftpd-hpa on port 69 serves all files.
- If you need to change the EEPROM config later, edit the `boot.conf` section in `prepare_netboot.sh` and re-run.
