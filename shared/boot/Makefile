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

# Map kernel/monorepo ARCH to U-Boot ARCH
# Note: U-Boot manages both 32-bit and 64-bit ARM under arch/arm
ifeq ($(ARCH),arm64)
  UBOOT_ARCH := arm
else
  UBOOT_ARCH := $(ARCH)
endif

# Prefer lld over ld.bfd — ld.bfd 2.38 has a known segfault on AArch64 under
# QEMU/Docker-on-Apple-Silicon when linking large ELFs (e.g. u-boot).
# Fall back to the default cross linker if lld is not installed.
ifneq ($(shell which ld.lld 2>/dev/null),)
  UBOOT_LD := LD=ld.lld
else
  UBOOT_LD :=
endif

# Prevent command-line overrides (such as BOARD=rpi4) from being passed
# down to U-Boot sub-make invocations. U-Boot defines its own internal BOARD
# variable based on CONFIG_SYS_BOARD (e.g. 'rpi', not 'rpi4'), and passing
# BOARD to U-Boot breaks its board directory resolution (BOARDDIR).
MAKEOVERRIDES :=
unexport BOARD

UBOOT_SRC ?= $(REPO_ROOT)/shared/boot/u-boot
BUILD_DIR ?= $(REPO_ROOT)/shared/boot/build/$(BOARD)

UBOOT_MAKE := $(MAKE) -C $(UBOOT_SRC) O=$(BUILD_DIR) ARCH=$(UBOOT_ARCH) CROSS_COMPILE=$(CROSS_COMPILE) $(UBOOT_LD)

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
	@echo "  make fetch-firmware [BOARD=<board>] Fetch binary firmware files for board"
	@echo "  make deploy-sd [BOARD=<board>]      Deploy boot artifacts to mounted SD card"

fetch-firmware:
	@echo "==> Fetching firmware for $(BOARD)..."
	@mkdir -p $(REPO_ROOT)/shared/boot/firmware/$(BOARD)
ifeq ($(BOARD),rpi4)
	@curl -s -L -o $(REPO_ROOT)/shared/boot/firmware/$(BOARD)/start4.elf https://raw.githubusercontent.com/raspberrypi/firmware/master/boot/start4.elf
	@curl -s -L -o $(REPO_ROOT)/shared/boot/firmware/$(BOARD)/fixup4.dat https://raw.githubusercontent.com/raspberrypi/firmware/master/boot/fixup4.dat
	@curl -s -L -o $(REPO_ROOT)/shared/boot/firmware/$(BOARD)/bcm2711-rpi-4-b.dtb https://raw.githubusercontent.com/raspberrypi/firmware/master/boot/bcm2711-rpi-4-b.dtb
else
	@echo "No firmware fetch defined for $(BOARD)"
endif


deploy-sd: build
	@$(REPO_ROOT)/tools/deploy/deploy_bootfs.sh $(BOARD)

$(BUILD_DIR):
	mkdir -p $(BUILD_DIR)

$(BUILD_DIR)/.config: | $(BUILD_DIR)
	@echo "==> Configuring U-Boot for $(BOARD) ($(UBOOT_DEFCONFIG))..."
	$(UBOOT_MAKE) $(UBOOT_DEFCONFIG)
ifneq ($(strip $(UBOOT_CONFIG_DISABLE)),)
	@for opt in $(UBOOT_CONFIG_DISABLE); do \
		echo "--> Disabling $$opt..."; \
		$(UBOOT_SRC)/scripts/config --file $(BUILD_DIR)/.config --disable $$opt; \
	done
	$(UBOOT_MAKE) olddefconfig
endif
ifneq ($(strip $(UBOOT_CONFIG_ENABLE)),)
	@for opt in $(UBOOT_CONFIG_ENABLE); do \
		echo "--> Enabling $$opt..."; \
		$(UBOOT_SRC)/scripts/config --file $(BUILD_DIR)/.config --enable $$opt; \
	done
	$(UBOOT_MAKE) olddefconfig
endif
	@echo "==> Preparing U-Boot build tree..."
	$(UBOOT_MAKE) prepare

defconfig: $(BUILD_DIR)/.config

build: $(BUILD_DIR)/.config
	@echo "==> Compiling U-Boot for $(BOARD)..."
	$(UBOOT_MAKE) -j$$(getconf _NPROCESSORS_ONLN 2>/dev/null || echo 4)
	@echo ""
	@echo "=========================================================="
	@echo "✔ U-Boot build completed for $(BOARD)!"
	@echo "  Binary: $(BUILD_DIR)/u-boot.bin"
	@echo "=========================================================="


menuconfig: $(BUILD_DIR)/.config
	$(UBOOT_MAKE) menuconfig

clean:
	@echo "==> Cleaning U-Boot build for $(BOARD)..."
	rm -rf $(BUILD_DIR)

distclean:
	@echo "==> Cleaning all boot build directories..."
	rm -rf $(REPO_ROOT)/shared/boot/build
