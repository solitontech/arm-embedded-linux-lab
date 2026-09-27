# Raspberry Pi 4 Documentation

This directory contains hardware documentation, board bringup guides, and platform references for the **Raspberry Pi 4 Model B** (Broadcom BCM2711, Quad-core Cortex-A72, ARM64/AArch64) within the ARM Embedded Linux Lab.

---

## Documents in this Directory

* [Raspberry Pi 4 Manual Linux Bringup Guide](manual_boot_guide.md)  
  *Complete, step-by-step manual procedure covering SD card partitioning, VideoCore firmware configuration (`config.txt`, `cmdline.txt`), custom AArch64 Linux kernel (`Image`) and Device Tree (`bcm2711-rpi-4-b.dtb`) cross-compilation, minimal BusyBox root filesystem creation, UART serial debugging, and U-Boot TFTP/NFS boot options.*

---

## Related Infrastructure References

* **Board Profile:** [`shared/build_system/boards/rpi4.mk`](../../shared/build_system/boards/rpi4.mk)
* **Serial Console:** `./lab console --board=rpi4`
* **Docker Environment:** [`tools/docker/run.sh`](../../tools/docker/run.sh)
