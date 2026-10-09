---
description: Build and update the BusyBox NFS root filesystem for a target board (currently RPi4 AArch64) and verify it boots over NFS via the Docker container's NFS server.
---

# NFS Root Filesystem Workflow

## When to Use This Workflow

- Rebuilding `nfs/rpi4-rootfs/` from source (e.g. after changing BusyBox config or adding applets).
- Adding userspace binaries, config files, or init scripts to the NFS rootfs.
- Setting up NFS boot on a new board by creating a `nfs/<board>-rootfs/` directory.
- Debugging NFS mount failures at boot.

## Prerequisites

- Docker container is built and can be started (`./tools/docker/run.sh build`). See `.agents/skills/docker-setup/SKILL.md`.
- BusyBox submodule is initialised: `git submodule update --init shared/rootfs/busybox`.
- The RPi4 kernel is built with NFS and IP_PNP compiled statically (`=y`). See `docs/raspi4/uboot_tftp_boot.md` section 3.1.
- SD card BOOT partition has the NFS `boot.scr` deployed (see section 3.4 of the same doc).

## Steps

### 1. Start the Docker container

```bash
./tools/docker/run.sh run
```

All subsequent commands run **inside the container** unless stated otherwise.

### 2. Configure BusyBox for static AArch64 build

```bash
cd /workspace/shared/rootfs/busybox
make ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- defconfig

# Enable static linking (no shared library dependencies on target)
sed -i 's/# CONFIG_STATIC is not set/CONFIG_STATIC=y/' .config

# Optional: open menuconfig to enable extra applets (e.g. vi, wget, nc)
# make ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- menuconfig
```

### 3. Build and install BusyBox into the NFS export directory

```bash
make -j$(nproc) ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu-
make install ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- CONFIG_PREFIX=/workspace/nfs/rpi4-rootfs
```

This populates `nfs/rpi4-rootfs/bin/busybox` and creates all symlinks in `bin/`, `sbin/`, `usr/bin/`, and `usr/sbin/`.

### 4. Create the required directory hierarchy

BusyBox `make install` does not create runtime-mounted directories. Create them manually (they are not committed — `rcS` mounts them at boot):

```bash
cd /workspace/nfs/rpi4-rootfs
mkdir -p dev proc sys tmp var/log root home
chmod 1777 tmp
```

### 5. Verify or create essential config files

Check that `etc/inittab` and `etc/init.d/rcS` exist and are correct. The committed versions work for a minimal serial-console boot. For SSH access, follow `docs/raspi4/rootfs_busybox.md` section 6 to add Dropbear.

```bash
cat /workspace/nfs/rpi4-rootfs/etc/inittab
cat /workspace/nfs/rpi4-rootfs/etc/init.d/rcS
```

### 6. Verify the NFS export is live

The container entrypoint starts the NFS server automatically. Confirm the export is active:

```bash
showmount -e localhost
# Expected output:
# Export list for localhost:
# /workspace/nfs  192.168.1.0/24
```

If the export is missing, re-run `exportfs -ra` as root inside the container:

```bash
sudo exportfs -ra
sudo exportfs -v
```

### 7. Boot the Raspberry Pi 4 and verify

Power on the Pi. In the serial console you should see:

```text
[    2.xxx] NFS: Mounting 192.168.1.220:/workspace/nfs/rpi4-rootfs on /
[    2.xxx] VFS: Mounted root (nfs filesystem) on device 0:14.
[    2.xxx] Run /sbin/init as init process
==========================================================
 Welcome to Soliton ARM Embedded Linux Lab — Pi 4 Bringup
 Kernel: 6.6.y on aarch64
==========================================================
Please press Enter to activate this console.
/ #
```

### 8. Commit the updated rootfs

```bash
# From the repo root on the host
git add nfs/rpi4-rootfs/
git commit -m "rootfs(nfs/rpi4): <description of change>"
```

Only commit files you intentionally changed. The `dev/`, `proc/`, `sys/`, `tmp/`, and `var/` directories should remain absent from the repository (they are created at runtime by `rcS`).

## Files Touched

- `[MODIFY]` `nfs/rpi4-rootfs/` — rebuilt BusyBox binary and symlinks
- `[MODIFY]` `nfs/rpi4-rootfs/etc/inittab` — if init config changed
- `[MODIFY]` `nfs/rpi4-rootfs/etc/init.d/rcS` — if startup script changed
- `[MODIFY]` `shared/bsp/rpi4/boot.cmd` + `boot.scr` — only if NFS path or IP changed

## Notes

- **Path contract**: The NFS export path `/workspace/nfs/rpi4-rootfs` must match the `nfsroot=` argument in `shared/bsp/rpi4/boot.cmd`. Do not move the directory without updating `boot.cmd` and recompiling `boot.scr`.
- **no_root_squash**: The NFS export uses `no_root_squash`. This is required for the kernel to create root-owned device nodes during mount. It also means the Pi's root user has full write access to the host-side directory — keep this on an isolated lab LAN.
- **WSL2 limitation**: `modprobe nfsd` requires the host kernel to include the `nfsd` module. The WSL2 Microsoft kernel does not include it. Use a native Linux host or a Linux VM for the NFS server in that case.
- **Adding a new board**: Create `nfs/<board>-rootfs/` following the same structure, add a corresponding `etc/exports` entry in `tools/docker/entrypoint.sh`, and update `shared/bsp/<board>/boot.cmd` with the correct `nfsroot=` path.
- **Related docs**: [nfs/README.md](../../nfs/README.md) | [docs/raspi4/uboot_tftp_boot.md](../../docs/raspi4/uboot_tftp_boot.md) | [docs/raspi4/rootfs_busybox.md](../../docs/raspi4/rootfs_busybox.md)
