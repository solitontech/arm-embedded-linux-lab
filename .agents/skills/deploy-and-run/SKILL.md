---
name: deploy-and-run
description: Build, deploy, run, and reboot target boards across multiple hardware architectures and projects using the unified easymake framework.
---

# Deploy and Run on Target Boards

## Purpose
Enables automated building, cross-compilation, deployment (SSH, TFTP, NFS), and hardware control (reboot, console, GDB) for any project in the monorepo.

## When to Use This Skill
- When building a project for a specific target board (`BOARD=rpi4`, `BOARD=rpi3`, `BOARD=beaglebone`, `BOARD=qemu_arm64`, `BOARD=host`)
- When deploying binaries or boot files to target hardware or lab servers
- When executing applications remotely or inspecting serial boot console
- When resetting a target board via U-Boot serial or SSH

## Prerequisites
- Target board environment file exists at `tools/deploy/boards/<board>.env` (copied from `tools/deploy/boards/<board>.env.example`)
- Cross-compiler toolchain is installed in the DevContainer or system environment

## Instructions

### Step 1: Inspect Target Configuration
Check compiler flags, architecture, deploy method, and network addresses:
```bash
lab info <project-name> --board <board-name>
```

### Step 2: Build Project
Cross-compile the project for the target board:
```bash
lab build <project-name> --board <board-name>
```

### Step 3: Deploy to Board
Deploy artifacts using the configured strategy (SSH, TFTP, or NFS):
```bash
lab deploy <project-name> --board <board-name>
```

### Step 4: Run Application Remotely
Execute the deployed binary over SSH and stream output:
```bash
lab run <project-name> --board <board-name>
```

### Step 5: Target Reset (If Needed)
Trigger target reset / reboot:
```bash
lab reboot --board <board-name>
```

## Notes
- Use `lab` as the primary CLI entry point for all build, deploy, and run operations — prefer `./lab <command>` over raw `make` calls.
- To simulate without modifying physical boards or networks, pass `--dry-run`: `lab deploy <project> --board <board> --dry-run` or `lab reboot --board <board> --dry-run`.
- All object files and binaries are segregated under `projects/<project>/build/<board>/`.
