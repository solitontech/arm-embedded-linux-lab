# nfs/ — NFS-Exported Root Filesystems

This directory holds pre-built root filesystems that the Docker container exports over NFS so target boards can mount their rootfs over the network — no SD card writes needed for userspace changes.

## Directory Layout

```
nfs/
└── rpi4-rootfs/      # BusyBox rootfs for Raspberry Pi 4 (AArch64)
    ├── bin/          # BusyBox multi-call binary + symlinks
    ├── sbin/         # System binaries (init, ifconfig, …)
    ├── usr/          # usr/bin and usr/sbin BusyBox applets
    ├── etc/
    │   ├── inittab         # BusyBox init: sysinit → rcS, askfirst → /bin/sh
    │   └── init.d/rcS      # Mounts proc/sys/devtmpfs, prints boot banner
    └── linuxrc       # Symlink → bin/busybox (for initramfs compatibility)
```

## How It Is Used

When the Docker container starts, `tools/docker/entrypoint.sh` exports `/workspace/nfs` (this directory, bind-mounted from the repo) over NFS to `192.168.1.0/24`. The RPi4 `boot.cmd` kernel argument `nfsroot=192.168.1.220:/workspace/nfs/rpi4-rootfs` tells the kernel to mount this directory as its root filesystem.

Any change made to files under `nfs/rpi4-rootfs/` on the host is visible to the board immediately on the next boot — no packaging or flashing step required.

See [docs/raspi4/uboot_tftp_boot.md](../docs/raspi4/uboot_tftp_boot.md) for end-to-end NFS boot setup and troubleshooting.

## How `rpi4-rootfs` Was Built

**Toolchain:** `aarch64-linux-gnu-gcc` (inside Docker container)
**BusyBox version:** v1.36.1 (statically linked, no shared library dependencies)

```bash
# Inside Docker container
cd /workspace/shared/rootfs/busybox
make defconfig
sed -i 's/# CONFIG_STATIC is not set/CONFIG_STATIC=y/' .config
make -j$(nproc) ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu-
make install CONFIG_PREFIX=/workspace/nfs/rpi4-rootfs
```

After installation, the directory structure (`etc/inittab`, `etc/init.d/rcS`, device node requirements) was completed following the steps in [docs/raspi4/rootfs_busybox.md](../docs/raspi4/rootfs_busybox.md).

To rebuild from scratch, follow [.agents/workflows/nfs_rootfs.md](../.agents/workflows/nfs_rootfs.md).

## Notes

- The `busybox` binary is the only real binary in the rootfs; everything else in `bin/`, `sbin/`, `usr/bin/`, and `usr/sbin/` is a symlink back to `../../bin/busybox` (BusyBox multi-call convention).
- `dev/`, `proc/`, `sys/`, `tmp/`, and `var/` directories are **not committed** — `rcS` mounts them dynamically at boot. If you need device nodes (`/dev/console`, `/dev/null`), create them with `mknod` inside the container after the NFS export is live, or add them to `rcS`.
- The rootfs has no password on `root`. It is intended for an isolated lab LAN only.
