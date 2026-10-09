---
name: lab-mcp
description: Connect to physical embedded Linux boards via the MCP Hardware Tool Bridge — serial console, boot analysis, BSP management, and bench verification.
---

# Lab MCP Server — Hardware Tool Bridge

## Purpose

Provides AI agents with governed access to physical embedded Linux boards via
the Model Context Protocol (MCP).  Implements the Hardware Tool Bridge from the
[Agentic FDLC](https://solitontech.com/agentic-firmware-development-lifecycle):
serial trace capture, boot log analysis, BSP modification, board reboot, and
tiered verification (Tier 1 host-side via Docker, Tier 2 bench via serial).

## When to Use This Skill

- You need to read boot logs or serial output from a physical board
- You need to diagnose why a board is stuck during boot (kernel panic, NFS timeout, etc.)
- You need to modify BSP files (boot.cmd, config.txt) and recompile boot.scr
- You need to reboot a board or execute commands on it via SSH
- You need to deploy files to TFTP, NFS rootfs, or SD card
- You need to run a full bench verification cycle (reboot → boot → analyze)
- You need to cross-compile inside the Docker container

## Prerequisites

- MCP server must be running: `./lab mcp status` to check, `./lab mcp start` to start
- Board must be configured in `shared/boards/<board>.env`
- Serial cable connected for serial tools
- Docker container running for `lab_docker_exec` and `lab_doctor`

## Available Tools

### Board Discovery
- **`lab_board_list()`** — List all boards with online/offline status
- **`lab_board_status(board)`** — Detailed status (ping, serial, SSH)
- **`lab_doctor()`** — Full diagnostics inside Docker

### Serial Console
- **`lab_serial_log(board, lines=100, pattern=None, since=None)`** — Read serial output
- **`lab_serial_send(board, text)`** — Send to serial (supports `\\r`, `\\n`, `\\x03`)
- **`lab_serial_wait(board, pattern, timeout_s=30)`** — Wait for regex match
- **`lab_serial_release(board)`** — Free port for manual access
- **`lab_serial_acquire(board)`** — Resume MCP monitoring

### Boot Analysis
- **`lab_boot_analyze(board)`** — Returns: boot stage, errors with diagnosis + fixes, parsed bootargs

### Board Control
- **`lab_reboot(board, method=None)`** — Reboot (uboot_serial, ssh, sysrq_serial, power_relay)
- **`lab_ssh_exec(board, command, timeout=30)`** — SSH command execution

### BSP Management
- **`lab_bsp_read(board, filename)`** — Read BSP file
- **`lab_bsp_write(board, filename, content)`** — Write BSP file (.bak backup)
- **`lab_bsp_compile(board)`** — Compile boot.cmd → boot.scr
- **`lab_bsp_deploy_sd(board)`** — Deploy to mounted SD card

### Build & Deploy
- **`lab_docker_exec(command, timeout=120)`** — Run command in Docker (Tier 1)
- **`lab_tftp_list(subdir=None)`** — List TFTP directory
- **`lab_nfs_list(board, path="/")`** — List NFS rootfs
- **`lab_nfs_write(board, path, content, mode="644")`** — Write to NFS rootfs

### Bench Verification
- **`lab_bench_verify(board, success_pattern, fail_patterns, timeout_s)`** — Full reboot→verify cycle
- **`lab_verify_report(board)`** — Generate VERIFICATION_REPORT.md

## Example Workflows

### Debug a Boot Failure

```
1. lab_serial_log(rpi4, lines=50)        # Read recent boot output
2. lab_boot_analyze(rpi4)                 # Get structured diagnosis
3. lab_bsp_read(rpi4, "boot.cmd")        # Check boot configuration
4. lab_bsp_write(rpi4, "boot.cmd", fix)  # Fix the issue
5. lab_bsp_compile(rpi4)                  # Recompile boot.scr
6. lab_bsp_deploy_sd(rpi4)               # Deploy to SD card
7. lab_bench_verify(rpi4)                 # Full reboot + verify
```

### Cross-compile and Deploy a Project

```
1. lab_docker_exec("./lab build hello_world --board rpi4")  # Tier 1 build
2. lab_nfs_write(rpi4, "usr/local/bin/hello", content)      # Deploy to NFS
3. lab_reboot(rpi4)                                          # Reboot board
4. lab_serial_wait(rpi4, "login:", timeout_s=60)             # Wait for boot
5. lab_ssh_exec(rpi4, "/usr/local/bin/hello")                # Run on target
```

### Monitor a Boot in Real-Time

```
1. lab_reboot(rpi4, method="uboot_serial")
2. lab_serial_wait(rpi4, "Hit any key", timeout_s=10)    # U-Boot prompt
3. lab_serial_send(rpi4, "\\r")                           # Let autoboot proceed
4. lab_serial_wait(rpi4, "login:|panic", timeout_s=60)   # Wait for outcome
5. lab_boot_analyze(rpi4)                                 # Analyze result
```

## Notes

- Serial logs persist across server restarts (disk-backed ring buffer)
- The boot analyzer includes `rule_suggestion` in each error — use it to update AGENT_RULES.md
- Only one process can hold a serial port — use release/acquire for manual access
- The server binds to 127.0.0.1 only — use SSH tunneling for remote access
