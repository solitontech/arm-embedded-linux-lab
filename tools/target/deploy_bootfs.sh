#!/usr/bin/env bash
set -e

BOARD=$1
MODE=${2:-dev}    # "dev" (default) or "prod"

if [ -z "$BOARD" ]; then
    echo "Usage: $0 <board> [dev|prod]"
    echo ""
    echo "  dev  — BOOT partition only (EEPROM netboot + NFS rootfs) [default]"
    echo "  prod — BOOT + flash SquashFS rootfs to partition 2"
    exit 1
fi

if [ "$MODE" != "dev" ] && [ "$MODE" != "prod" ]; then
    echo "Error: mode must be 'dev' or 'prod', got '$MODE'"
    exit 1
fi

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
BOOT_BUILD_DIR="$REPO_ROOT/shared/boot/build/$BOARD"
# BSP dir: committed firmware blobs, DTB, config.txt, cmdline.txt
BSP_DIR="$REPO_ROOT/shared/bsp/$BOARD"
# NOTE: The kernel Image is not stored in the repo (too large).
# Build it in Docker and copy it to the SD card manually, or add a
# KERNEL_IMAGE variable here pointing to your local build output.

# Detect OS
OS_NAME="$(uname -s)"
MOUNT_POINT=""

if [ "$OS_NAME" = "Darwin" ]; then
    if [ -d "/Volumes/bootfs" ]; then
        MOUNT_POINT="/Volumes/bootfs"
    elif [ -d "/Volumes/BOOT" ]; then
        MOUNT_POINT="/Volumes/BOOT"
    fi
elif [ "$OS_NAME" = "Linux" ]; then
    # Typical auto-mount locations for Linux
    if [ -d "/media/$USER/BOOT" ]; then
        MOUNT_POINT="/media/$USER/BOOT"
    elif [ -d "/media/$USER/bootfs" ]; then
        MOUNT_POINT="/media/$USER/bootfs"
    elif [ -d "/mnt/bootfs" ]; then
        MOUNT_POINT="/mnt/bootfs"
    fi
elif [[ "$OS_NAME" == MINGW* ]] || [[ "$OS_NAME" == CYGWIN* ]]; then
    # Windows fallback
    echo "Windows detected. Please copy the files manually or specify mount point."
    exit 1
fi

if [ -z "$MOUNT_POINT" ]; then
    echo "Error: Could not find boot volume. Please ensure SD card is mounted."
    exit 1
fi

echo "==> Deploying boot artifacts to $MOUNT_POINT"

# Clean the boot partition safely
if [[ "$MOUNT_POINT" == *"/bootfs" ]] || [[ "$MOUNT_POINT" == *"/BOOT" ]]; then
    echo "  -> Cleaning existing files in $MOUNT_POINT"
    rm -rf "${MOUNT_POINT:?}/"*
else
    echo "Warning: Mount point does not end with /bootfs or /BOOT. Skipping cleanup for safety."
fi

# Copy pre-built U-Boot binary (built in Docker or committed in BSP)
if [ -f "$BOOT_BUILD_DIR/u-boot.bin" ]; then
    cp "$BOOT_BUILD_DIR/u-boot.bin" "$MOUNT_POINT/"
    echo "  -> Copied u-boot.bin"
elif [ -f "$BSP_DIR/u-boot.bin" ]; then
    cp "$BSP_DIR/u-boot.bin" "$MOUNT_POINT/"
    echo "  -> Copied u-boot.bin"
else
    echo "  [WARN] u-boot.bin not found in $BOOT_BUILD_DIR or $BSP_DIR!"
    echo "         Build it inside Docker: cd shared/boot && make BOARD=$BOARD"
fi

# Compile boot.cmd -> boot.scr (U-Boot script image) if mkimage is available
BOOT_CMD="$BSP_DIR/boot.cmd"
BOOT_SCR="$BSP_DIR/boot.scr"
if [ -f "$BOOT_CMD" ]; then
    if command -v mkimage >/dev/null 2>&1; then
        echo "  -> Compiling boot.cmd -> boot.scr..."
        mkimage -C none -A arm64 -T script -d "$BOOT_CMD" "$BOOT_SCR" >/dev/null
        echo "  -> Compiled boot.scr"
    else
        echo "  [WARN] mkimage not found — skipping boot.scr compilation."
        echo "         To compile inside Docker: mkimage -C none -A arm64 -T script -d shared/bsp/rpi4/boot.cmd shared/bsp/rpi4/boot.scr"
    fi
fi

# Production mode: copy kernel Image to BOOT partition (loaded by U-Boot from SD)
if [ "$MODE" = "prod" ]; then
    KERNEL_IMAGE="$REPO_ROOT/tftp/Image"
    if [ -f "$KERNEL_IMAGE" ]; then
        cp "$KERNEL_IMAGE" "$MOUNT_POINT/"
        echo "  -> Copied kernel Image ($(du -h "$KERNEL_IMAGE" | cut -f1)) to BOOT partition"
    else
        echo "  [ERROR] Kernel Image not found at $KERNEL_IMAGE"
        echo "          Build it: ./lab docker exec -- bash -c 'cd shared/kernel && make BOARD=rpi4 deploy-tftp'"
        exit 1
    fi
fi

# Copy committed BSP files to BOOT partition.
# boot.cmd is intentionally excluded — it is a source file only.
# U-Boot reads boot.scr (the compiled binary). boot.cmd has no effect on the target.
if [ -d "$BSP_DIR" ]; then
    for f in "$BSP_DIR"/*; do
        fname="$(basename "$f")"
        case "$fname" in
            boot.cmd)
                echo "  -> Skipping $fname (source file only)"
                ;;
            Image)
                echo "  -> Skipping $fname (handled separately)"
                ;;
            u-boot.bin)
                # u-boot.bin is already handled above (with BOOT_BUILD_DIR fallback)
                ;;
            *)
                cp "$f" "$MOUNT_POINT/"
                echo "  -> Copied $fname"
                ;;
        esac
    done
else
    echo "  [WARN] BSP directory not found: $BSP_DIR"
fi

# --- Production mode: flash SquashFS to partition 2 ---
if [ "$MODE" = "prod" ]; then
    # Locate the SquashFS image
    SQUASHFS="$REPO_ROOT/shared/buildroot/buildroot/output/images/rootfs.squashfs"
    if [ ! -f "$SQUASHFS" ]; then
        # Try project-local Buildroot output
        SQUASHFS="$REPO_ROOT/projects/vision-edge/buildroot/output/images/rootfs.squashfs"
    fi

    if [ ! -f "$SQUASHFS" ]; then
        echo "  [ERROR] rootfs.squashfs not found!"
        echo "          Build it first: cd shared/buildroot/buildroot && make"
        exit 1
    fi

    # Derive the rootfs partition device from the BOOT mount point
    ROOTFS_DEV=""
    if [ "$OS_NAME" = "Linux" ]; then
        # Find which device is mounted at BOOT, then use partition 2
        BOOT_DEV="$(findmnt -n -o SOURCE "$MOUNT_POINT" 2>/dev/null || true)"
        if [ -n "$BOOT_DEV" ]; then
            # /dev/sdX1 -> /dev/sdX2, /dev/mmcblk0p1 -> /dev/mmcblk0p2
            ROOTFS_DEV="$(echo "$BOOT_DEV" | sed 's/1$/2/')"
        fi
    elif [ "$OS_NAME" = "Darwin" ]; then
        BOOT_DEV="$(diskutil info "$MOUNT_POINT" 2>/dev/null | awk '/Device Node/ {print $NF}' || true)"
        if [ -n "$BOOT_DEV" ]; then
            ROOTFS_DEV="$(echo "$BOOT_DEV" | sed 's/s1$/s2/')"
        fi
    fi

    if [ -z "$ROOTFS_DEV" ]; then
        echo "  [ERROR] Could not determine rootfs partition device."
        echo "          Ensure the SD card has a partition 2 (see docs/raspi4/sd_card_setup.md)"
        exit 1
    fi

    echo "  -> Flashing SquashFS to $ROOTFS_DEV ..."
    echo "     Source: $SQUASHFS ($(du -h "$SQUASHFS" | cut -f1))"

    # Unmount partition 2 if mounted
    if mountpoint -q "$ROOTFS_DEV" 2>/dev/null; then
        sudo umount "$ROOTFS_DEV" 2>/dev/null || true
    fi
    # Also unmount any auto-mounted ROOTFS label
    for mp in "/media/$USER/ROOTFS" "/media/$USER/rootfs" "/tmp/rpi-rootfs"; do
        if [ -d "$mp" ] && mountpoint -q "$mp" 2>/dev/null; then
            sudo umount "$mp" 2>/dev/null || true
        fi
    done

    sudo dd if="$SQUASHFS" of="$ROOTFS_DEV" bs=4M status=progress
    echo "  -> SquashFS flashed to $ROOTFS_DEV"
fi

# Sync the filesystem
sync

echo ""
echo "==> Deploy complete! (mode: $MODE)"
echo "    BOOT partition ($MOUNT_POINT):"
echo "      start4.elf, fixup4.dat  — GPU firmware"
echo "      config.txt              — kernel=u-boot.bin, enable_uart=1"
echo "      u-boot.bin              — second-stage bootloader"
echo "      boot.scr                — U-Boot autoboot script (dev/prod auto-detect)"
echo "      bcm2711-rpi-4-b.dtb     — DTB for U-Boot hardware init"
if [ "$MODE" = "prod" ]; then
    echo "    ROOTFS partition ($ROOTFS_DEV):"
    echo "      rootfs.squashfs         — production SquashFS (read-only)"
    echo ""
    echo "    Boot mode: PRODUCTION (SquashFS on partition 2)"
else
    echo "    TFTP boot (served by Docker container):"
    echo "      Image                   — place in /workspace/tftp/Image"
    echo "      bcm2711-rpi-4-b.dtb     — place in /workspace/tftp/"
    echo ""
    echo "    Boot mode: DEVELOPMENT (EEPROM netboot + NFS rootfs)"
    echo "    To switch to production: $0 $BOARD prod"
fi
