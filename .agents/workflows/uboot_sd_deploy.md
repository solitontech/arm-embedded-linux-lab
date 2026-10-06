---
description: how to fetch, build, and deploy U-Boot bootloader artifacts to an SD card
---

# U-Boot Bootloader Deployment Workflow

## When to Use This Workflow
When you need to prepare a fresh SD card for a hardware board (like the Raspberry Pi 4) that uses U-Boot as the bootloader, and you need to fetch proprietary firmware, build the U-Boot binary, and deploy them to the SD card.

## Prerequisites
- Target board profile must be configured in `shared/build_system/boards/`.
- SD Card must be partitioned correctly (a FAT32 boot partition named `bootfs` or `BOOT`) and mounted on the host OS.

## Steps

1. **Fetch Firmware**
   Download the proprietary GPU firmware (e.g. `start4.elf`, `fixup4.dat` for RPi4) and device trees for the board.
   ```bash
   cd shared/boot
   make fetch-firmware BOARD=rpi4
   ```

2. **Configure Boot Parameters & Boot Script (If Needed)**
   Modify or create the board's `config.txt`, `cmdline.txt`, and U-Boot boot script (`boot.cmd`).
   - Edit `shared/boot/configs/<board>/config.txt`
   - Edit `shared/boot/configs/<board>/cmdline.txt`
   - Edit `shared/bsp/<board>/boot.cmd` (e.g. TFTP network boot commands)

3. **Build and Deploy to SD Card**
   Cross-compile U-Boot and invoke the cross-platform deploy script to copy the binary, firmware, configurations, and compiled `boot.scr` to the mounted SD card. This script compiles `boot.cmd` -> `boot.scr` (via `mkimage` from `u-boot-tools`) and cleans the existing boot partition before copying.
   ```bash
   cd shared/boot
   make deploy-sd BOARD=rpi4
   ```
   Or invoke the deployment helper directly:
   ```bash
   ./tools/deploy/deploy_bootfs.sh rpi4
   ```

4. **Verify**
   Check the terminal output to ensure `u-boot.bin`, `boot.scr`, firmware files, and configuration files were copied. You can now safely eject the SD card and boot the hardware.

## Files Touched
- `[MODIFY]` `shared/boot/configs/<board>/config.txt` (Optional)
- `[MODIFY]` `shared/boot/configs/<board>/cmdline.txt` (Optional)

## Notes
- The deploy script (`tools/deploy/deploy_bootfs.sh`) dynamically detects macOS and Linux mount points.
- U-Boot compilation requires the cross-compiler toolchain, usually handled inside the monorepo Docker container.
