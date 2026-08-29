# ==============================================================================
# Board Profile: BeagleBone Black
# Hardware: TI AM335x, Single-core Cortex-A8 (ARMv7-A 32-bit hard float)
# ==============================================================================

BOARD_NAME        := beaglebone
BOARD_DESC        := BeagleBone Black (TI AM335x, Cortex-A8 ARMv7-A)
ARCH              := arm
CROSS_COMPILE     ?= arm-linux-gnueabihf-

# Architecture & Optimization Flags
CPU_FLAGS         := -march=armv7-a -mtune=cortex-a8 -mfpu=neon -mfloat-abi=hard
BOARD_CFLAGS      := $(CPU_FLAGS)
BOARD_CXXFLAGS    := $(CPU_FLAGS)
BOARD_LDFLAGS     := 

# Default lab deployment preference for this board profile
DEFAULT_DEPLOY    := tftp
