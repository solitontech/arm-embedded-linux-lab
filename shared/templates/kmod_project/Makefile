# ==============================================================================
# Out-of-tree kernel module template
# Build in Docker:  ./lab docker exec make -C projects/<name>
# Deploy to rootfs: ./lab docker exec make -C projects/<name> deploy
# Load on target:   ./lab ssh -- insmod /lib/modules/<ver>/extra/<name>.ko
# ==============================================================================

MODULE_NAME ?= hello

# Kbuild part (read by the kernel build system, which sets KERNELRELEASE)
obj-m := $(MODULE_NAME).o

ifeq ($(KERNELRELEASE),)
BOARD ?= rpi4

# Repo root = nearest parent containing shared/build_system, so the project can
# sit at any depth (projects/<name>, projects/<group>/<name>, ...)
REPO_ROOT ?= $(shell d="$(CURDIR)"; while [ "$$d" != "/" ] && [ ! -d "$$d/shared/build_system" ]; do d=$$(dirname "$$d"); done; echo "$$d")

# Board profile supplies ARCH, CROSS_COMPILE and KDIR
include $(REPO_ROOT)/shared/build_system/boards/$(BOARD).mk

NFS_ROOT  ?= $(REPO_ROOT)/nfs/$(BOARD)-rootfs
# Module.symvers only exists after a full kernel link. Without it modpost cannot
# resolve kernel symbols at build time, so unresolved symbols are downgraded to
# warnings and are checked by the kernel at insmod time (safe: KDIR matches the
# running kernel). Drop MODPOST_WARN after a full `make -C shared/kernel build`.
MODPOST_WARN ?= 1
KBUILD    := $(MAKE) -C $(KDIR) M=$(CURDIR) ARCH=$(ARCH) CROSS_COMPILE=$(CROSS_COMPILE) KBUILD_MODPOST_WARN=$(MODPOST_WARN)

.PHONY: all clean deploy compdb
all:
	@test -f $(KDIR)/.config || { echo "KDIR $(KDIR) not ready: run 'make -C shared/kernel BOARD=$(BOARD) build modules-prepare'"; exit 1; }
	$(KBUILD) modules

clean:
	$(KBUILD) clean

# Optional: compile_commands.json for clangd. Run in Docker after a build; paths
# inside the container are /workspace/...; pass HOST_ROOT=<host repo path> to rewrite them.
compdb: all
	python3 $(KDIR)/../../rpi-linux/scripts/clang-tools/gen_compile_commands.py -d $(CURDIR) -o $(CURDIR)/compile_commands.json
	@if [ -n "$(HOST_ROOT)" ]; then sed -i 's#$(REPO_ROOT)#$(HOST_ROOT)#g' compile_commands.json; fi

# Install the .ko into the NFS rootfs the board mounts, then refresh modules.dep
deploy: all
	$(eval KVER := $(shell cat $(KDIR)/include/config/kernel.release))
	install -D -m644 $(MODULE_NAME).ko $(NFS_ROOT)/lib/modules/$(KVER)/extra/$(MODULE_NAME).ko
	@touch $(NFS_ROOT)/lib/modules/$(KVER)/modules.order $(NFS_ROOT)/lib/modules/$(KVER)/modules.builtin
	depmod -b $(NFS_ROOT) $(KVER)
	@echo "==> Deployed. On target: insmod /lib/modules/$(KVER)/extra/$(MODULE_NAME).ko"
endif
