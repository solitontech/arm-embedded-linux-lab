# ==============================================================================
# rules.mk
# Standard targets and lifecycle management for monorepo projects.
# ==============================================================================

.PHONY: all build clean distclean deploy run reboot console gdb info help

# Default target
all: build

# Build target with pre and post build hooks
build: $(PRE_BUILD_HOOK) $(TARGET) $(POST_BUILD_HOOK)
	@echo "  [DONE] Built $(PROJECT_NAME) for $(BOARD) -> $(TARGET)"

# Clean the current board's build artifacts
clean:
	@echo "  [CLEAN] Removing $(BUILD_DIR)..."
	@rm -rf $(BUILD_DIR)

# Clean all boards' build artifacts for this project
distclean:
	@echo "  [DISTCLEAN] Removing build/ directory..."
	@rm -rf build

# ------------------------------------------------------------------------------
# Deployment Targets
# ------------------------------------------------------------------------------

# Deploy target
deploy: build $(PRE_DEPLOY_HOOK)
	@echo "======================================================================"
	@echo "  [DEPLOY] Project: $(PROJECT_NAME) -> Board: $(BOARD) ($(DEPLOY_METHOD))"
	@echo "======================================================================"
	@$(DEPLOY_SCRIPT) \
		--board="$(BOARD)" \
		--method="$(DEPLOY_METHOD)" \
		--files="$(DEPLOY_FILES)" \
		--dest-dir="$(TARGET_DEST_DIR)" \
		--target-ip="$(TARGET_IP)" \
		--target-user="$(TARGET_USER)" \
		--target-port="$(TARGET_PORT)" \
		--target-key="$(TARGET_SSH_KEY)" \
		--tftp-base="$(TFTP_BASE_DIR)" \
		--tftp-sub="$(BOARD_TFTP_SUBDIR)" \
		--nfs-base="$(NFS_BASE_DIR)" \
		--nfs-rootfs="$(BOARD_NFS_ROOTFS)" \
		--lab-host-ip="$(LAB_HOST_IP)" \
		--lab-host-user="$(LAB_HOST_USER)" \
		--lab-host-key="$(LAB_SSH_KEY)"
	@$(MAKE) --no-print-directory $(POST_DEPLOY_HOOK)
	@echo "  [DONE] Deployment completed."

# Run on target (deploys if needed, then executes remotely)
run: deploy
	@echo "  [RUN] Executing $(TARGET_DEST_DIR)/$(PROJECT_NAME) on $(BOARD)..."
	@if [ -n "$(TARGET_IP)" ]; then \
		ssh -o BatchMode=yes -o StrictHostKeyChecking=no \
			$${TARGET_PORT:+-p $$TARGET_PORT} \
			$${TARGET_SSH_KEY:+-i $$TARGET_SSH_KEY} \
			$(TARGET_USER)@$(TARGET_IP) "$(TARGET_DEST_DIR)/$(PROJECT_NAME)"; \
	else \
		echo "  [ERROR] TARGET_IP not configured in tools/deploy/boards/$(BOARD).env"; \
		exit 1; \
	fi

# Reboot target board
reboot:
	@echo "  [REBOOT] Triggering reboot for board: $(BOARD)..."
	@$(REBOOT_SCRIPT) \
		--board="$(BOARD)" \
		--method="$(BOARD_RESET_METHOD)" \
		--serial-port="$(BOARD_SERIAL_PORT)" \
		--serial-baud="$(BOARD_SERIAL_BAUD)" \
		--reset-cmd="$(BOARD_RESET_CMD)" \
		--target-ip="$(TARGET_IP)" \
		--target-user="$(TARGET_USER)" \
		--target-key="$(TARGET_SSH_KEY)"

# Open serial console to target board
console:
	@echo "  [CONSOLE] Connecting to $(BOARD) on $(BOARD_SERIAL_PORT)..."
	@$(CONSOLE_SCRIPT) \
		--board="$(BOARD)" \
		--serial-port="$(BOARD_SERIAL_PORT)" \
		--serial-baud="$(BOARD_SERIAL_BAUD)"

# Remote GDB debug session
gdb: build
	@echo "  [GDB] Launching cross GDB for $(TARGET)..."
	@$(GDB_SCRIPT) \
		--target-elf="$(TARGET)" \
		--cross-gdb="$(CROSS_COMPILE)gdb" \
		--target-ip="$(TARGET_IP)" \
		--gdb-port="$(GDB_PORT)"

# ------------------------------------------------------------------------------
# Information & Help
# ------------------------------------------------------------------------------

info:
	@echo "======================================================================"
	@echo " Project Configuration: $(PROJECT_NAME)"
	@echo "======================================================================"
	@echo " Project Name    : $(PROJECT_NAME)"
	@echo " Project Type    : $(PROJECT_TYPE)"
	@echo " Target Board    : $(BOARD) - $(BOARD_DESC)"
	@echo " Target Binary   : $(TARGET)"
	@echo " Deploy Method   : $(DEPLOY_METHOD)"
	@echo " Target Dest Dir : $(TARGET_DEST_DIR)"
	@echo " Architecture    : $(ARCH)"
	@echo " Toolchain       : $(CROSS_COMPILE)gcc / g++"
	@echo " CPU Flags       : $(CPU_FLAGS)"
	@echo " CFLAGS          : $(CFLAGS)"
	@echo " CXXFLAGS        : $(CXXFLAGS)"
	@echo " LDFLAGS         : $(LDFLAGS)"
	@echo " LDLIBS          : $(LDLIBS)"
	@echo " Target IP       : $(if $(TARGET_IP),$(TARGET_IP),<not set in $(BOARD).env>)"
	@echo " Target User     : $(TARGET_USER)"
	@echo " Serial Port     : $(if $(BOARD_SERIAL_PORT),$(BOARD_SERIAL_PORT),<not set in $(BOARD).env>)"
	@echo " Reset Method    : $(BOARD_RESET_METHOD)"
	@echo " TFTP Base / Sub : $(TFTP_BASE_DIR) / $(BOARD_TFTP_SUBDIR)"
	@echo " NFS Base / Sub  : $(NFS_BASE_DIR) / $(BOARD_NFS_ROOTFS)"
	@echo "======================================================================"

help:
	@echo "Available Targets:"
	@echo "  make [all|build] [BOARD=<name>]  - Build project for target board (default: $(DEFAULT_BOARD))"
	@echo "  make clean                       - Clean build artifacts for active board"
	@echo "  make distclean                   - Clean all build artifacts"
	@echo "  make deploy [BOARD=<name>]       - Deploy artifacts to target (SSH / TFTP / NFS)"
	@echo "  make run [BOARD=<name>]          - Deploy and execute binary on target"
	@echo "  make reboot [BOARD=<name>]       - Reset / reboot target board"
	@echo "  make console [BOARD=<name>]      - Open serial console (picocom/minicom)"
	@echo "  make gdb [BOARD=<name>]          - Start cross-GDB session"
	@echo "  make info [BOARD=<name>]         - Display resolved configuration and environment"
