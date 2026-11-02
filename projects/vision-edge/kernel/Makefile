obj-m := vision_safety.o

# Point KDIR at the kernel source tree used for cross-compilation.
# Override on the command line if your tree is elsewhere:
#   make KDIR=/path/to/linux-source
KDIR  ?= /workspace/buildroot/output/build/linux-custom
PWD   := $(shell pwd)

default:
	$(MAKE) -C $(KDIR) M=$(PWD) modules ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu-

clean:
	$(MAKE) -C $(KDIR) M=$(PWD) clean
