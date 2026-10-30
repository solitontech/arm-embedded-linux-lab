# ==============================================================================
# ARM Embedded Linux Lab — Kernel Build System
# Builds the Linux kernel for any board profile defined in shared/build_system/boards/
# Follows the same pattern as shared/boot/Makefile (U-Boot).
# ==============================================================================

BOARD ?= rpi4
REPO_ROOT ?= $(shell cd ../.. && pwd)
BOARDS_DIR := $(REPO_ROOT)/shared/build_system/boards
BOARD_MK := $(BOARDS_DIR)/$(BOARD).mk

ifeq ($(wildcard $(BOARD_MK)),)
  $(error Board profile '$(BOARD)' not found at $(BOARD_MK))
endif

include $(BOARD_MK)

KERNEL_SRC := $(REPO_ROOT)/shared/kernel/rpi-linux
BUILD_DIR  := $(REPO_ROOT)/shared/kernel/build/$(BOARD)
BSP_DIR    := $(REPO_ROOT)/shared/bsp/$(BOARD)
TFTP_DIR   := $(REPO_ROOT)/tftp
NFS_DIR    := $(REPO_ROOT)/shared/nfs/$(BOARD)-rootfs

NPROC := $(shell getconf _NPROCESSORS_ONLN 2>/dev/null || echo 4)

KERNEL_MAKE := $(MAKE) -C $(KERNEL_SRC) O=$(BUILD_DIR) \
	ARCH=arm64 CROSS_COMPILE=$(CROSS_COMPILE) -j$(NPROC)

# Default defconfig per board
ifeq ($(BOARD),rpi4)
  KERNEL_DEFCONFIG ?= bcm2711_defconfig
endif

# Optional config fragments (e.g. camera_kconfig.cfg)
CONFIG_FRAGMENTS := $(wildcard $(BSP_DIR)/*_kconfig.cfg)

.PHONY: all defconfig menuconfig build modules_install dtbs \
        deploy-tftp deploy-modules clean distclean help

all: build

help:
	@echo "ARM Embedded Linux Lab - Kernel Build System"
	@echo "Usage:"
	@echo "  make [BOARD=<board>]                Build kernel Image + modules + DTBs"
	@echo "  make defconfig [BOARD=<board>]      Generate .config from board defconfig"
	@echo "  make menuconfig [BOARD=<board>]     Interactive kernel configuration"
	@echo "  make dtbs [BOARD=<board>]           Build Device Tree Blobs only"
	@echo "  make deploy-tftp [BOARD=<board>]    Copy Image + DTB to TFTP directory"
	@echo "  make deploy-modules [BOARD=<board>] Install modules to NFS rootfs"
	@echo "  make clean [BOARD=<board>]          Clean build artifacts"
	@echo "  make distclean                      Clean all board builds"

$(BUILD_DIR):
	mkdir -p $(BUILD_DIR)

# Generate .config from defconfig, then merge any config fragments
$(BUILD_DIR)/.config: | $(BUILD_DIR)
	@echo "==> Configuring kernel for $(BOARD) ($(KERNEL_DEFCONFIG))..."
	$(KERNEL_MAKE) $(KERNEL_DEFCONFIG)
ifneq ($(strip $(CONFIG_FRAGMENTS)),)
	@echo "==> Merging config fragments: $(notdir $(CONFIG_FRAGMENTS))"
	cd $(KERNEL_SRC) && \
	  ARCH=arm64 scripts/kconfig/merge_config.sh \
	    -O $(BUILD_DIR) $(BUILD_DIR)/.config $(CONFIG_FRAGMENTS)
endif

defconfig: $(BUILD_DIR)/.config

menuconfig: $(BUILD_DIR)/.config
	$(KERNEL_MAKE) menuconfig

build: $(BUILD_DIR)/.config
	@echo "==> Building kernel for $(BOARD)..."
	$(KERNEL_MAKE) Image modules dtbs
	@echo "==> Kernel build complete: $(BUILD_DIR)/arch/arm64/boot/Image"

dtbs: $(BUILD_DIR)/.config
	$(KERNEL_MAKE) dtbs

# Deploy kernel + DTB to TFTP directory (Docker serves this)
deploy-tftp: build
	@mkdir -p $(TFTP_DIR)
	@echo "==> Deploying Image + DTB to $(TFTP_DIR)/"
	cp $(BUILD_DIR)/arch/arm64/boot/Image $(TFTP_DIR)/Image
ifeq ($(BOARD),rpi4)
	cp $(BUILD_DIR)/arch/arm64/boot/dts/broadcom/bcm2711-rpi-4-b.dtb $(TFTP_DIR)/
	@if [ -d $(BUILD_DIR)/arch/arm64/boot/dts/overlays ]; then \
		mkdir -p $(TFTP_DIR)/overlays; \
		grep -oP '(?<=dtoverlay=)\S+' $(BSP_DIR)/config.txt 2>/dev/null | while read ov; do \
			src="$(BUILD_DIR)/arch/arm64/boot/dts/overlays/$${ov}.dtbo"; \
			if [ -f "$$src" ]; then \
				cp "$$src" $(TFTP_DIR)/overlays/; \
				echo "==> Copied overlay: $${ov}.dtbo"; \
			else \
				echo "WARN: overlay $${ov}.dtbo not found in kernel build"; \
			fi; \
		done; \
	fi
endif
	@echo "==> TFTP deployment complete."

# Install kernel modules to NFS rootfs
deploy-modules: build
	@mkdir -p $(NFS_DIR)
	@echo "==> Installing modules to $(NFS_DIR)/"
	$(KERNEL_MAKE) modules_install INSTALL_MOD_PATH=$(NFS_DIR)
	@echo "==> Module installation complete."

clean:
	@echo "==> Cleaning kernel build for $(BOARD)..."
	@rm -rf $(BUILD_DIR)

distclean:
	@echo "==> Cleaning all kernel builds..."
	@rm -rf $(REPO_ROOT)/shared/kernel/build
