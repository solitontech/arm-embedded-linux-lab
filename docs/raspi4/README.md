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
| [Network Boot Deep Dive](netboot_deep_dive.md) | Technical architecture, DHCP/dnsmasq deep dive, and case studies |
| [Wireless Setup & Credentials](wifi_setup.md) | Enabling on-board Wi-Fi, firmware, and secure credential isolation |

---

## Monorepo Integration Checklist

Once your board boots successfully into userspace:

- [x] Serial console working via `./lab console --board=rpi4`
- [x] Kernel + DTB served over TFTP (Docker container running)
- [x] BusyBox NFS rootfs built and exported from Docker NFS server
- [x] U-Boot PXE boot via `pxelinux.cfg/default` with NFS root
- [x] EEPROM reprogrammed with `BOOT_ORDER=0xf12` (network-first, SD-card eliminated)
- [x] dnsmasq DHCP inside Docker, TFTP from `/workspace/tftp/`
- [x] Dropbear SSH: `./lab ssh --board=rpi4`
- [x] Build and deploy projects: `./lab build --project=<name> --board=rpi4`
- [x] Run diagnostics: `./lab doctor` (inside Docker)

---

## Related Infrastructure

* **Board Profile:** [`shared/build_system/boards/rpi4.mk`](../../shared/build_system/boards/rpi4.mk)
* **BSP Assets:** [`shared/bsp/rpi4/`](../../shared/bsp/rpi4/)
* **Serial Console:** `./lab console --board=rpi4`
* **Docker Environment:** `./lab docker`
