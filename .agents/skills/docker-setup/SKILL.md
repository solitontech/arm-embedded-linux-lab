---
name: docker-setup
description: Build and run a reproducible Docker development environment for the ARM Embedded Linux Lab on any OS (macOS, Linux, Windows).
---

# Docker Setup Skill

## Purpose
Provide a reproducible cross-compilation environment without requiring developers to install toolchains manually. The Docker image contains all compilers, serial tools, and deploy utilities pre-installed.

## When to Use This Skill
- On a fresh workstation (macOS, Linux, Windows with Docker Desktop / WSL2).
- In CI pipelines that need cross-compilation.
- When `lab doctor` reports missing toolchains and you cannot or do not want to install them natively.
- When onboarding a new team member who needs the lab environment immediately.

## Prerequisites
- Docker Desktop (macOS / Windows) or Docker Engine (Linux) installed.
  - macOS: https://docs.docker.com/desktop/mac/install/
  - Linux: https://docs.docker.com/engine/install/
  - Windows: https://docs.docker.com/desktop/windows/install/ (enable WSL2 backend)
- The repository must be cloned locally.

## Included Toolchains & Tools

| Package | Purpose |
|---|---|
| `gcc`, `g++`, `clang` | Native host compilation |
| `gcc-aarch64-linux-gnu`, `g++-aarch64-linux-gnu` | ARM64 cross-compiler (RPi4, RPi3, QEMU) |
| `gcc-arm-linux-gnueabihf`, `g++-arm-linux-gnueabihf` | ARM32 cross-compiler (BeagleBone Black) |
| `gdb-multiarch` | Multi-arch GDB debugger |
| `picocom`, `minicom`, `socat` | Serial UART console & bridging tools |
| `nano` | Terminal text editor |
| `ssh`, `rsync`, `scp` | Remote deploy utilities |
| `tftpd-hpa`, `tftp-hpa` | TFTP server & client utilities for network boot/deploy |
| `iproute2` | Advanced IP networking tools (`ip`, `ss`, etc.) |
| `bison`, `flex`, `bc` | Parser generators and math utilities for kernel & U-Boot |
| `libssl-dev`, `swig` | Cryptographic and interface compiler libraries |
| `device-tree-compiler` | `dtc` for compiling Device Tree blobs (`.dtb`) and overlays |
| `lld` | High-performance LLVM linker (avoids binutils ld.bfd emulation bugs on Apple Silicon) |
| `u-boot-tools` | `mkimage` and `dumpimage` for compiling U-Boot script images (`boot.scr`) and FIT images |

## Instructions

### Step 1: Install Docker on Host (If Not Already Installed)
If Docker is not installed on the workstation, run the automated installer:
```bash
./tools/docker/run.sh install-docker
```
- On **macOS**: Installs Docker Desktop via Homebrew Cask and launches it.
- On **Linux**: Installs Docker via the official Docker convenience script and adds the current user to the `docker` group.
- On **Windows**: Installs Docker Desktop via `winget`.

### Step 2: Build the Lab Docker Image
From the repository root:
```bash
./tools/docker/run.sh build
```
This reads `tools/docker/Dockerfile` and builds an image tagged `arm-embedded-linux-lab:latest`.
The host UID/GID are passed as build args to avoid file permission issues.

### Step 3: Start an Interactive Container
```bash
./tools/docker/run.sh run
```
The repository root is bind-mounted at `/workspace` inside the container. All source edits on the host are immediately visible inside the container and vice-versa.

### Step 4: Stop or Close Existing Container Environments
To kill or close existing running container sessions and clean up host bridges:
```bash
./tools/docker/run.sh stop
```
This gracefully stops and removes `arm-lab-dev` and terminates any host-side `socat` serial bridges.

### Step 5: Reconnect to a Running Container Session
If your terminal disconnects or times out while the container is running:
```bash
./tools/docker/run.sh attach
```
This re-opens an interactive shell inside the existing container without losing state or restarting the TFTP server daemon.

### Step 6: Use the `lab` CLI Inside the Container
Inside the container shell:
```bash
./lab doctor            # verify all toolchains are present
./lab list              # list boards and projects
./lab build myproject --board rpi4
./lab deploy myproject --board rpi4 --dry-run
```

### Step 7: Run a Single Command Without an Interactive Shell
```bash
./tools/docker/run.sh exec ./lab build myproject --board rpi4
```

### Step 8: Push Image to Registry (CI / Team Use)
```bash
REGISTRY=ghcr.io/your-org ./tools/docker/run.sh push
```

## Notes
- The container runs as a non-root user (`labuser`) matching the host UID/GID, with passwordless `sudo` and membership in `dialout`.
- **Serial ports are detected and passed in automatically across platforms:**
  - **Linux host**: Directly enumerates all `/dev/ttyUSB*` and `/dev/ttyACM*` devices and passes them via `--device`.
  - **macOS host**: Docker Desktop runs in a virtual machine and cannot directly mount `/dev/cu.*` character devices via `--device`. `run.sh` automatically detects macOS serial adapters (`/dev/cu.usbserial*`, `/dev/cu.usbmodem*`), launches background host `socat` TCP listeners, and the container entrypoint creates corresponding `/dev/ttyVUSB<N>` PTY devices and `/dev/ttyUSB<N>` compatibility symlinks. `picocom`, `minicom`, and `./lab console` work directly out of the box.
- To use a custom image tag: `IMAGE_TAG=v1.2 ./tools/docker/run.sh build`.

## Reproducible TFTP Server & Host Networking

The Docker container runs with `--network host` to expose the TFTP server on UDP port 69 directly on the host PC's LAN IP.

- **Persistent TFTP Directory**: The TFTP root is pre-configured to `/workspace/tftp` (bind-mounted from the host repository). Files like `test.txt` or kernel/bootloader images remain persistent across container recreations.
- **Automated Container Entrypoint**: `/usr/local/bin/entrypoint.sh` automatically configures `/etc/default/tftpd-hpa`, fixes read permissions (`chmod -R a+rX /workspace/tftp`), starts `in.tftpd` on container startup, and executes commands as `labuser`.
- **Host Firewall (UFW) Requirement**: If UFW firewall is active on the host PC, allow incoming UDP TFTP requests by running on host:
  ```bash
  sudo ufw allow 69/udp
  ```
- **Board Verification (Target / Raspberry Pi)**:
  From target board or network client:
  ```bash
  tftp <HOST_LAN_IP> -c get test.txt
  ```

## Docker Layer Caching & Dockerfile Modifications

To ensure fast rebuild times when adding or updating packages:

- **Modular `RUN` Layers**: The `Dockerfile` is structured into ordered `RUN` steps:
  1. **Layer 1 (Core Host Tools)**: `build-essential`, `gcc`, `g++`, `clang`, `git`, `cmake`
  2. **Layer 2 (Heavy Cross-Compilers)**: `gcc-aarch64-linux-gnu`, `gcc-arm-linux-gnueabihf` (takes ~90% of total build time)
  3. **Layer 3 (Peripheral Utilities & Network Tools)**: `gdb-multiarch`, `picocom`, `minicom`, `nano`, `iproute2`, `tftp-hpa`, `tftpd-hpa`, `u-boot-tools`
- **Adding New Packages**: Always add new packages to **Layer 3** (or append a new `RUN apt-get update && apt-get install ...` layer at the end).
- **Cache Preservation**: When modifying Layer 3, Docker reuses cached layers for Layer 1 and Layer 2 (`---> Using cache`), allowing the build to complete in seconds rather than rebuilding heavy cross-compiler toolchains from scratch.
