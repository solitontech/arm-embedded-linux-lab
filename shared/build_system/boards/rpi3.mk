# ==============================================================================
# Board Profile: Raspberry Pi 3 Model B+ / Zero 2W
# Hardware: Broadcom BCM2837B0, Quad-core Cortex-A53 (ARMv8-A 64-bit)
# ==============================================================================

BOARD_NAME        := rpi3
BOARD_DESC        := Raspberry Pi 3 Model B+ / Zero 2W (BCM2837, Cortex-A53 ARM64)
ARCH              := arm64
CROSS_COMPILE     ?= aarch64-linux-gnu-

# Architecture & Optimization Flags
CPU_FLAGS         := -mcpu=cortex-a53+crc
BOARD_CFLAGS      := $(CPU_FLAGS)
BOARD_CXXFLAGS    := $(CPU_FLAGS)
BOARD_LDFLAGS     := 

# Default lab deployment preference for this board profile
DEFAULT_DEPLOY    := ssh
