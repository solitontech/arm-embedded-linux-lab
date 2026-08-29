# ==============================================================================
# easymake_base.mk
# Standard AArch64 compile flags shared across all projects utilizing 
# the Cortex-A72 cores (e.g. Raspberry Pi 4). 
# Projects simply `include ../../shared/build_system/easymake_base.mk`
# ==============================================================================

CC := aarch64-linux-gnu-gcc
CXX := aarch64-linux-gnu-g++

# Enable C++20 and optimize (BOARD_OPT_FLAGS can be passed in per-board)
CXXFLAGS := -std=c++20 -O2 \
            $(BOARD_OPT_FLAGS) \
            -Wall -Wextra -Wpedantic \
            -I../../shared/lib/include

CFLAGS := -O2 \
          $(BOARD_OPT_FLAGS) \
          -Wall -Wextra

# Standard link paths if needed
LDFLAGS := -pthread
