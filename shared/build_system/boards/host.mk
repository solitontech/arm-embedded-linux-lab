# ==============================================================================
# Board Profile: Native Host (Development & Testing)
# Uses the system's native compiler — no cross-compilation.
# ==============================================================================

BOARD_NAME        := host
BOARD_DESC        := Native host build (development & testing)
ARCH              := $(shell uname -m)
CROSS_COMPILE     :=

# No architecture-specific flags for host builds
CPU_FLAGS         :=
BOARD_CFLAGS      :=
BOARD_CXXFLAGS    :=
BOARD_LDFLAGS     :=

# No deployment for host builds
DEFAULT_DEPLOY    := none
