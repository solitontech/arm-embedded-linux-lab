# ==============================================================================
# Out-of-tree kernel module template
# Build in Docker:  ./lab docker exec make -C projects/<name>
# Deploy to rootfs: ./lab docker exec make -C projects/<name> deploy
# Load on target:   ./lab ssh -- insmod /lib/modules/<ver>/extra/<name>.ko
#
# All build output (.o, .cmd, .mod*, Module.symvers, <name>.ko) goes to
# build/<board>/ so the project folder only holds your sources. Kbuild (6.6)
# cannot build external modules out-of-tree itself, so sources are symlinked into
# build/<board>/ together with a generated Kbuild file.
# ==============================================================================

MODULE_NAME ?= hello
# Add more .c files here for a multi-file module (first entry may be <name>.c)
MODULE_SRCS ?= $(MODULE_NAME).c
BOARD       ?= rpi4

# Repo root = nearest parent containing shared/build_system, so the project can
# sit at any depth (projects/<name>, projects/<group>/<name>, ...)
REPO_ROOT ?= $(shell d="$(CURDIR)"; while [ "$$d" != "/" ] && [ ! -d "$$d/shared/build_system" ]; do d=$$(dirname "$$d"); done; echo "$$d")

# Board profile supplies ARCH, CROSS_COMPILE and KDIR
include $(REPO_ROOT)/shared/build_system/boards/$(BOARD).mk

NFS_ROOT  ?= $(REPO_ROOT)/nfs/$(BOARD)-rootfs
SRC_DIR   := $(CURDIR)
BUILD_DIR := $(CURDIR)/build/$(BOARD)

# Module.symvers only exists after a full kernel link. Without it modpost cannot
# resolve kernel symbols at build time, so unresolved symbols are downgraded to
# warnings and are checked by the kernel at insmod time (safe: KDIR matches the
# running kernel). Drop MODPOST_WARN after a full `make -C shared/kernel build`.
MODPOST_WARN ?= 1
KBUILD    := $(MAKE) -C $(KDIR) M=$(BUILD_DIR) ARCH=$(ARCH) CROSS_COMPILE=$(CROSS_COMPILE) KBUILD_MODPOST_WARN=$(MODPOST_WARN)

# A composite module (several sources) needs <name>-objs; a single <name>.c must not.
ifneq ($(MODULE_SRCS),$(MODULE_NAME).c)
KBUILD_OBJS_LINE := echo "$(MODULE_NAME)-objs := $(MODULE_SRCS:.c=.o)";
endif

.DEFAULT_GOAL := all
.PHONY: all stage clean deploy compdb

# Link sources into the build dir and generate its Kbuild file
stage:
	@test -f $(KDIR)/.config || { echo "KDIR $(KDIR) not ready: run 'make -C shared/kernel BOARD=$(BOARD) kdir-from-image ...' (see kernel-module-dev skill)"; exit 1; }
	@mkdir -p $(BUILD_DIR)
	@for f in $(MODULE_SRCS); do ln -sf $(SRC_DIR)/$$f $(BUILD_DIR)/$$f; done
	@{ echo "obj-m := $(MODULE_NAME).o"; $(KBUILD_OBJS_LINE) echo "ccflags-y += -I$(SRC_DIR)"; } > $(BUILD_DIR)/Kbuild

all: stage
	$(KBUILD) modules

clean:
	rm -rf $(BUILD_DIR)

# Optional: compile_commands.json for clangd (written to the build dir). Run in Docker
# after a build; paths inside the container are /workspace/...; pass
# HOST_ROOT=<host repo path> to rewrite them.
compdb: all
	python3 $(KDIR)/../../rpi-linux/scripts/clang-tools/gen_compile_commands.py -d $(BUILD_DIR) -o $(BUILD_DIR)/compile_commands.json
	@if [ -n "$(HOST_ROOT)" ]; then sed -i 's#$(REPO_ROOT)#$(HOST_ROOT)#g' $(BUILD_DIR)/compile_commands.json; fi

# Install the .ko into the NFS rootfs the board mounts, then refresh modules.dep
deploy: all
	$(eval KVER := $(shell cat $(KDIR)/include/config/kernel.release))
	install -D -m644 $(BUILD_DIR)/$(MODULE_NAME).ko $(NFS_ROOT)/lib/modules/$(KVER)/extra/$(MODULE_NAME).ko
	@touch $(NFS_ROOT)/lib/modules/$(KVER)/modules.order $(NFS_ROOT)/lib/modules/$(KVER)/modules.builtin
	depmod -b $(NFS_ROOT) $(KVER)
	@echo "==> Deployed. On target: insmod /lib/modules/$(KVER)/extra/$(MODULE_NAME).ko"
