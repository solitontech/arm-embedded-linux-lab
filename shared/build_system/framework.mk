# ==============================================================================
# framework.mk
# Master build & deploy framework entrypoint for ARM Embedded Linux Lab.
# ==============================================================================

# ------------------------------------------------------------------------------
# 1. Path Resolution
# ------------------------------------------------------------------------------
FRAMEWORK_DIR := $(abspath $(dir $(lastword $(MAKEFILE_LIST))))
REPO_ROOT     := $(abspath $(FRAMEWORK_DIR)/../..)

# ------------------------------------------------------------------------------
# 2. Project Metadata Defaults
# ------------------------------------------------------------------------------
PROJECT_NAME  ?= $(notdir $(CURDIR))
PROJECT_TYPE  ?= app
DEFAULT_BOARD ?= rpi4

# Target board resolution (Command-line BOARD overrides DEFAULT_BOARD)
BOARD ?= $(DEFAULT_BOARD)

# Check if board definition file exists
BOARD_MK_FILE := $(FRAMEWORK_DIR)/boards/$(BOARD).mk
ifeq ($(wildcard $(BOARD_MK_FILE)),)
  AVAILABLE_BOARDS := $(patsubst $(FRAMEWORK_DIR)/boards/%.mk,%,$(wildcard $(FRAMEWORK_DIR)/boards/*.mk))
  $(error Unknown BOARD '$(BOARD)'. Available boards: $(AVAILABLE_BOARDS))
endif

# Load board architecture & hardware profile
include $(BOARD_MK_FILE)

# ------------------------------------------------------------------------------
# 3. Lab Environment & Secrets Loading (Git-Ignored .env files)
# ------------------------------------------------------------------------------
-include $(REPO_ROOT)/tools/deploy/lab_host.env
-include $(REPO_ROOT)/tools/deploy/boards/$(BOARD).env

# Connectivity defaults if not explicitly set in .env
TARGET_USER          ?= root
TARGET_PORT          ?= 22
BOARD_RESET_METHOD   ?= uboot_serial
BOARD_SERIAL_BAUD    ?= 115200
GDB_PORT             ?= 2345
BOARD_TFTP_SUBDIR    ?= $(BOARD)
BOARD_NFS_ROOTFS     ?= $(BOARD)/rootfs

# Deployment defaults
DEPLOY_METHOD        ?= $(DEFAULT_DEPLOY)
TARGET_DEST_DIR      ?= /usr/local/bin

# ------------------------------------------------------------------------------
# 4. Toolchain & Paths
# ------------------------------------------------------------------------------
CC    := $(CROSS_COMPILE)gcc
CXX   := $(CROSS_COMPILE)g++
LD    := $(CROSS_COMPILE)g++
AR    := $(CROSS_COMPILE)ar
STRIP := $(CROSS_COMPILE)strip

BUILD_DIR := build/$(BOARD)

ifeq ($(PROJECT_TYPE),lib_static)
  TARGET ?= $(BUILD_DIR)/lib$(PROJECT_NAME).a
else ifeq ($(PROJECT_TYPE),lib_shared)
  TARGET ?= $(BUILD_DIR)/lib$(PROJECT_NAME).so
else
  TARGET ?= $(BUILD_DIR)/$(PROJECT_NAME)
endif

DEPLOY_FILES ?= $(TARGET)

# Script tools
DEPLOY_SCRIPT  := $(REPO_ROOT)/tools/deploy/deploy.sh
REBOOT_SCRIPT  := $(REPO_ROOT)/tools/deploy/reboot.sh
CONSOLE_SCRIPT := $(REPO_ROOT)/tools/deploy/console.sh
GDB_SCRIPT     := $(REPO_ROOT)/tools/deploy/gdb.sh

# ------------------------------------------------------------------------------
# 5. Compiler & Linker Flags Composition
# ------------------------------------------------------------------------------
CFLAGS   := -O2 -Wall -Wextra $(BOARD_CFLAGS) $(CFLAGS_EXTRA) \
            -I$(REPO_ROOT)/shared/lib/include $(INCLUDES_EXTRA)

CXXFLAGS := -std=c++20 -O2 -Wall -Wextra -Wpedantic $(BOARD_CXXFLAGS) $(CXXFLAGS_EXTRA) \
            -I$(REPO_ROOT)/shared/lib/include $(INCLUDES_EXTRA)

LDFLAGS  := $(BOARD_LDFLAGS) $(LDFLAGS_EXTRA)
LDLIBS   := -pthread $(LDLIBS_EXTRA)

# ------------------------------------------------------------------------------
# 6. Include Easymake Engine & Standard Targets
# ------------------------------------------------------------------------------
include $(FRAMEWORK_DIR)/easymake_base.mk
include $(FRAMEWORK_DIR)/rules.mk
