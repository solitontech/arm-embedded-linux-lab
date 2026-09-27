# ==============================================================================
# ARM Embedded Linux Lab — Bootloader Build System
# Builds U-Boot for any board profile defined in shared/build_system/boards/
# ==============================================================================

BOARD ?= rpi4
REPO_ROOT ?= $(shell cd ../.. && pwd)
BOARDS_DIR := $(REPO_ROOT)/shared/build_system/boards
BOARD_MK := $(BOARDS_DIR)/$(BOARD).mk

ifeq ($(wildcard $(BOARD_MK)),)
  $(error Board profile '$(BOARD)' not found at $(BOARD_MK))
endif

include $(BOARD_MK)

ifeq ($(UBOOT_DEFCONFIG),)
  $(error Board '$(BOARD)' does not define UBOOT_DEFCONFIG in $(BOARD_MK))
endif

UBOOT_SRC ?= $(REPO_ROOT)/shared/boot/u-boot
BUILD_DIR ?= $(REPO_ROOT)/shared/boot/build/$(BOARD)

.PHONY: all defconfig build clean distclean menuconfig help

all: build

help:
	@echo "ARM Embedded Linux Lab - Bootloader (U-Boot) Build System"
	@echo "Usage:"
	@echo "  make [BOARD=<board_name>]           Build U-Boot for target board (default: rpi4)"
	@echo "  make defconfig [BOARD=<board_name>] Generate default .config for target board"
	@echo "  make menuconfig [BOARD=<board_name>] Run interactive ncurses menuconfig"
	@echo "  make clean [BOARD=<board_name>]     Clean build artifacts for target board"
	@echo "  make distclean                      Clean all target board build directories"

$(BUILD_DIR):
	mkdir -p $(BUILD_DIR)

$(BUILD_DIR)/.config: | $(BUILD_DIR)
	@echo "==> Configuring U-Boot for $(BOARD) ($(UBOOT_DEFCONFIG))..."
	$(MAKE) -C $(UBOOT_SRC) O=$(BUILD_DIR) ARCH=$(ARCH) CROSS_COMPILE=$(CROSS_COMPILE) $(UBOOT_DEFCONFIG)

defconfig: $(BUILD_DIR)/.config

build: $(BUILD_DIR)/.config
	@echo "==> Compiling U-Boot for $(BOARD)..."
	$(MAKE) -C $(UBOOT_SRC) O=$(BUILD_DIR) ARCH=$(ARCH) CROSS_COMPILE=$(CROSS_COMPILE) -j$$(nproc)
	@echo ""
	@echo "=========================================================="
	@echo "✔ U-Boot build completed for $(BOARD)!"
	@echo "  Binary: $(BUILD_DIR)/u-boot.bin"
	@echo "=========================================================="

menuconfig: $(BUILD_DIR)/.config
	$(MAKE) -C $(UBOOT_SRC) O=$(BUILD_DIR) ARCH=$(ARCH) CROSS_COMPILE=$(CROSS_COMPILE) menuconfig

clean:
	@echo "==> Cleaning U-Boot build for $(BOARD)..."
	rm -rf $(BUILD_DIR)

distclean:
	@echo "==> Cleaning all boot build directories..."
	rm -rf $(REPO_ROOT)/shared/boot/build
