#!/usr/bin/env bash
set -e

BOARD=$1
if [ -z "$BOARD" ]; then
    echo "Usage: $0 <board>"
    exit 1
fi

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
BOOT_BUILD_DIR="$REPO_ROOT/shared/boot/build/$BOARD"
# BSP dir: committed firmware blobs (start4.elf, fixup4.dat, DTB)
BSP_DIR="$REPO_ROOT/shared/bsp/$BOARD"
CONFIG_DIR="$REPO_ROOT/shared/boot/configs/$BOARD"
# Kernel Image: built locally, not committed (too large)
KERNEL_IMAGE="$REPO_ROOT/shared/kernel/rpi-linux/arch/arm64/boot/Image"

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

# Copy pre-built U-Boot binary (built in Docker)
if [ -f "$BOOT_BUILD_DIR/u-boot.bin" ]; then
    cp "$BOOT_BUILD_DIR/u-boot.bin" "$MOUNT_POINT/"
    echo "  -> Copied u-boot.bin"
fi

# Copy committed BSP blobs: GPU firmware + DTB
if [ -d "$BSP_DIR" ]; then
    cp -r "$BSP_DIR"/* "$MOUNT_POINT/"
    echo "  -> Copied BSP files (start4.elf, fixup4.dat, DTB)"
else
    echo "  [WARN] BSP directory not found: $BSP_DIR"
fi

# Copy locally-built kernel Image (must be built first in Docker)
if [ -f "$KERNEL_IMAGE" ]; then
    cp "$KERNEL_IMAGE" "$MOUNT_POINT/"
    echo "  -> Copied kernel Image"
else
    echo "  [WARN] Kernel Image not found at $KERNEL_IMAGE — build it first in Docker"
fi

if [ -d "$CONFIG_DIR" ]; then
    cp "$CONFIG_DIR"/* "$MOUNT_POINT/"
    echo "  -> Copied configuration files"
fi

# Sync the filesystem
sync

echo "==> Deploy complete!"
