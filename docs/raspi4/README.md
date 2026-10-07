# Raspberry Pi 4 Documentation

> **BCM2711** | Quad-core Cortex-A72 | ARM64/AArch64

Step-by-step guides for manual Linux bringup on the Raspberry Pi 4 Model B — from bare-metal SD card boot through to fully SD-card-free network boot.

---

## Guides

| Guide | Description |
|---|---|
| [Boot Architecture & Hardware Setup](boot_architecture.md) | Boot pipeline, hardware BOM, serial UART wiring |
| [SD Card Setup](sd_card_setup.md) | Partitioning, VideoCore firmware, `config.txt`, `cmdline.txt` |
| [Kernel Cross-Compilation](kernel_build.md) | Building the Linux kernel, DTB, and modules for AArch64 |
| [BusyBox Root Filesystem](rootfs_busybox.md) | Minimal userspace with statically linked BusyBox |
| [U-Boot, TFTP & NFS Boot](uboot_tftp_boot.md) | First boot, TFTP iteration loop, NFS rootfs, troubleshooting |
| [EEPROM Network Boot](eeprom_netboot.md) | Eliminating the SD card entirely via EEPROM + dnsmasq |

---

## Monorepo Integration Checklist

Once your board boots successfully into userspace:

- [x] Serial console working via `./lab console --board=rpi4`
- [x] Kernel + DTB served over TFTP (Docker container running)
- [ ] BusyBox NFS rootfs built and exported from host
- [ ] `boot.cmd` updated to `root=/dev/nfs nfsroot=...`
- [ ] EEPROM reprogrammed with `BOOT_ORDER=0xf241` (optional, for SD-card elimination)
- [ ] dnsmasq configured and serving firmware from `/srv/tftp/rpi4/`
- [x] Build and deploy projects: `./lab build --project=<name> --board=rpi4`
- [x] Run diagnostics: `./lab doctor` (inside Docker)

---

## Related Infrastructure

* **Board Profile:** [`shared/build_system/boards/rpi4.mk`](../../shared/build_system/boards/rpi4.mk)
* **BSP Assets:** [`shared/bsp/rpi4/`](../../shared/bsp/rpi4/)
* **Serial Console:** `./lab console --board=rpi4`
* **Docker Environment:** `./lab docker`
