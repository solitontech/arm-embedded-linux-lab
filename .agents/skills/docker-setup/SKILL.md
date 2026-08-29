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
| `gdb-multiarch` | Multi-arch GDB debugger |
| `picocom`, `minicom` | Serial UART console |
| `ssh`, `rsync`, `scp` | Remote deploy utilities |

## Instructions

### Step 1: Build the Image
From the repository root:
```bash
./tools/docker/run.sh build
```
This reads `tools/docker/Dockerfile` and builds an image tagged `arm-embedded-linux-lab:latest`.
The host UID/GID are passed as build args to avoid file permission issues.

### Step 2: Start an Interactive Container
```bash
./tools/docker/run.sh run
```
The repository root is bind-mounted at `/workspace` inside the container. All source edits on the host are immediately visible inside the container and vice-versa.

### Step 3: Use the `lab` CLI Inside the Container
Inside the container shell:
```bash
./lab doctor            # verify all toolchains are present
./lab list              # list boards and projects
./lab build myproject --board rpi4
./lab deploy myproject --board rpi4 --dry-run
```

### Step 4: Run a Single Command Without an Interactive Shell
```bash
./tools/docker/run.sh exec ./lab build myproject --board rpi4
```

### Step 5: Push Image to Registry (CI / Team Use)
```bash
REGISTRY=ghcr.io/your-org ./tools/docker/run.sh push
```

## Notes
- The container runs as a non-root user (`labuser`) matching the host UID/GID.
- Serial ports (`/dev/ttyUSB*`, `/dev/ttyACM*`) must be passed to the container explicitly using `--device` if needed for console access.
- To use a custom image tag: `IMAGE_TAG=v1.2 ./tools/docker/run.sh build`.
