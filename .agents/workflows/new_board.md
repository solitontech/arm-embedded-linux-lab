---
description: how to add a new hardware board profile to the monorepo
---

# Add a New Board Profile

## When to Use This Workflow
Use this workflow when adding support for a new hardware platform or controller (e.g. Raspberry Pi 5, NXP i.MX8, STM32MP1, RISC-V) to the monorepo.

## Prerequisites
- Knowledge of the CPU architecture (e.g. ARMv8-A Cortex-A76, ARMv7-A Cortex-A9), toolchain prefix (`CROSS_COMPILE`), and required compiler tuning flags.
- Physical connection / lab host details (Serial device, IP, baud rate, reset method).

## Steps

1. **Create the hardware architecture profile (Committed)**
   Create `shared/build_system/boards/<board-name>.mk`:
   ```makefile
   BOARD_NAME     := <board-name>
   BOARD_DESC     := My Board Name (SoC / CPU Description)
   ARCH           := arm64   # arm64, arm, riscv64, x86_64
   CROSS_COMPILE  ?= aarch64-linux-gnu-

   # CPU architecture optimization flags
   CPU_FLAGS      := -mcpu=cortex-a72
   BOARD_CFLAGS   := $(CPU_FLAGS)
   BOARD_CXXFLAGS := $(CPU_FLAGS)
   BOARD_LDFLAGS  := 

   DEFAULT_DEPLOY := ssh     # ssh | tftp | nfs
   ```

2. **Create the committed lab environment template**
   Create `tools/deploy/boards/<board-name>.env.example`:
   ```bash
   TARGET_IP="192.168.1.xxx"
   TARGET_USER="root"
   TARGET_PORT="22"
   TARGET_DEST_DIR="/usr/local/bin"

   BOARD_SERIAL_PORT="/dev/ttyUSB0"
   BOARD_SERIAL_BAUD="115200"
   BOARD_RESET_METHOD="uboot_serial"   # uboot_serial | ssh | sysrq_serial | power_relay
   BOARD_RESET_CMD="reset\r"

   BOARD_TFTP_SUBDIR="<board-name>"
   BOARD_NFS_ROOTFS="<board-name>/rootfs"
   ```

3. **Create your local lab environment file (Git-Ignored)**
   ```bash
   cp tools/deploy/boards/<board-name>.env.example tools/deploy/boards/<board-name>.env
   ```
   Fill in your actual lab IP and `/dev/ttyUSB*` port.

4. **Verify board registration**
   ```bash
   make list-boards
   ```

5. **Test building and deploying a project**
   ```bash
   make info BOARD=<board-name>
   ```

## Files Touched
- `[CREATE]` `shared/build_system/boards/<board-name>.mk` (Committed)
- `[CREATE]` `tools/deploy/boards/<board-name>.env.example` (Committed)
- `[CREATE]` `tools/deploy/boards/<board-name>.env` (Git-ignored, local only)
