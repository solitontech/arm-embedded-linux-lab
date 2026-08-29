# ==============================================================================
# Project Makefile Template
# Copy to projects/<your-project>/ and set PROJECT_NAME and BOARD_OPT_FLAGS.
# ==============================================================================

PROJECT_NAME := my-project

# Set per-board CPU optimization flags before including the shared base.
# Example: export BOARD_OPT_FLAGS=-mcpu=cortex-a72  (Raspberry Pi 4)
#          export BOARD_OPT_FLAGS=-mcpu=cortex-a53  (Raspberry Pi 3 / Zero 2W)
BOARD_OPT_FLAGS ?=

# Pull in shared compiler configuration (toolchain, C++20 flags, include paths)
include ../../shared/build_system/easymake_base.mk

TARGET := build/$(BOARD)/$(PROJECT_NAME)

# Easymake discovers all .cpp files under src/ automatically
include easymake.mk
