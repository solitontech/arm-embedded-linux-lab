# ==============================================================================
# Board Profile: Raspberry Pi 4 Model B
# Hardware: Broadcom BCM2711, Quad-core Cortex-A72 (ARMv8-A 64-bit)
# ==============================================================================

BOARD_NAME        := rpi4
BOARD_DESC        := Raspberry Pi 4 Model B (BCM2711, Cortex-A72 ARM64)
ARCH              := arm64
CROSS_COMPILE     ?= aarch64-linux-gnu-

# Architecture & Optimization Flags
CPU_FLAGS         := -mcpu=cortex-a72+crc+crypto
BOARD_CFLAGS      := $(CPU_FLAGS)
BOARD_CXXFLAGS    := $(CPU_FLAGS)
BOARD_LDFLAGS     := 

# Bootloader Configuration
UBOOT_DEFCONFIG   := rpi_4_defconfig

# U-Boot Kconfig options to disable after applying defconfig.
# EFI_LOADER uses ELF shared objects incompatible with lld-14 on AArch64/QEMU.
# Embedded Linux bringup does not require UEFI runtime services.
UBOOT_CONFIG_DISABLE := EFI_LOADER EFI_HAVE_CAPSULE_SUPPORT EFI_CAPSULE_FIRMWARE_MANAGEMENT

# Default lab deployment preference for this board profile
DEFAULT_DEPLOY    := ssh
