#!/usr/bin/env bash
set -e

BOARD=$1
if [ -z "$BOARD" ]; then
    echo "Usage: $0 <board>"
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

# Copy committed BSP: GPU firmware, DTB, config.txt, cmdline.txt
if [ -d "$BSP_DIR" ]; then
    cp -r "$BSP_DIR"/* "$MOUNT_POINT/"
    echo "  -> Copied BSP files (firmware, DTB, config.txt, cmdline.txt, boot.scr)"
else
    echo "  [WARN] BSP directory not found: $BSP_DIR"
fi

# Sync the filesystem
sync

echo "==> Deploy complete!"
echo "    NOTE: Copy your kernel Image to $MOUNT_POINT/Image manually if needed."
echo "    TFTP boot: Place Image and bcm2711-rpi-4-b.dtb in /workspace/tftp/ on host."
