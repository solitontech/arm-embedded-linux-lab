# ==============================================================================
# Board Profile: Host (Native Workstation / Development Machine)
# Target: Native machine (x86_64 or arm64/Apple Silicon)
# ==============================================================================

BOARD_NAME        := host
BOARD_DESC        := Native Host Machine (Local compilation & testing)
ARCH              := native
CROSS_COMPILE     ?= 

# Architecture & Optimization Flags
CPU_FLAGS         := 
BOARD_CFLAGS      := 
BOARD_CXXFLAGS    := 
BOARD_LDFLAGS     := 

# Default deployment preference
DEFAULT_DEPLOY    := custom
