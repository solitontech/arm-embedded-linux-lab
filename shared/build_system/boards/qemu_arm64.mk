# ==============================================================================
# Board Profile: QEMU ARM64 (Virt Machine)
# Hardware: QEMU 'virt' machine, Cortex-A72 (ARMv8-A 64-bit)
# ==============================================================================

BOARD_NAME        := qemu_arm64
BOARD_DESC        := QEMU Virt Platform (ARM64 Cortex-A72 emulation)
ARCH              := arm64
CROSS_COMPILE     ?= aarch64-linux-gnu-

# Architecture & Optimization Flags
CPU_FLAGS         := -mcpu=cortex-a72
BOARD_CFLAGS      := $(CPU_FLAGS)
BOARD_CXXFLAGS    := $(CPU_FLAGS)
BOARD_LDFLAGS     := 

# Default lab deployment preference for this board profile
DEFAULT_DEPLOY    := ssh
