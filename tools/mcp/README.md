# ARM Embedded Linux Lab — MCP Server (Hardware Tool Bridge)

A persistent MCP server that gives AI agents governed access to physical embedded
Linux boards.  Implements the **Hardware Tool Bridge** described in the
[Agentic FDLC blog](https://solitontech.com/agentic-firmware-development-lifecycle).

## Architecture

```
AI Agent (Devin / Cursor / etc.)          Linux Host Machine
  MCP config: serverUrl →            ┌── lab-mcp-server (systemd) ──┐
  http://localhost:8420/sse          │  SerialManager  (ring buffer) │
  (via SSH -L 8420:localhost:8420)   │  BoardManager   (ping/SSH)    │
                                      │  BSPManager     (boot.cmd)    │
                                      │  DockerBridge   (Tier 1)      │
                                      │  BootAnalyzer   (diagnosis)   │
                                      │  DeployManager  (TFTP/NFS)    │
                                      │  BenchVerifier  (Tier 2)      │
                                      └─────────────────────────────────┘
```

## Quick Start

```bash
# 1. Create virtual environment and install dependencies
./lab mcp setup

# 2. Start the MCP server as a systemd user service
./lab mcp start

# 3. Check status
./lab mcp status

# 4. View logs
./lab mcp logs
```

## MCP Client Configuration

### Devin CLI

The repo includes `.devin/config.json` that configures the MCP server automatically.
When connecting from a remote machine, set up an SSH tunnel first:

```bash
ssh -L 8420:localhost:8420 user@linux-host
```

### Other AI Agents (Cursor, Windsurf, etc.)

Add to your MCP configuration:

```json
{
  "mcpServers": {
    "lab": {
      "serverUrl": "http://localhost:8420/sse"
    }
  }
}
```

## Tools Reference (22 tools)

### Board Discovery & Status

| Tool | Description |
|---|---|
| `lab_board_list` | List all configured boards with online/offline status |
| `lab_board_status(board)` | Detailed status: ping, serial, SSH, reset method |
| `lab_doctor` | Full lab diagnostics via Docker |

### Serial Console

| Tool | Description |
|---|---|
| `lab_serial_log(board, lines, pattern, since)` | Read serial output (ring buffer) |
| `lab_serial_send(board, text)` | Send to serial port (U-Boot cmds, Ctrl-C) |
| `lab_serial_wait(board, pattern, timeout_s)` | Wait for regex in serial output |
| `lab_serial_release(board)` | Release port for picocom/minicom |
| `lab_serial_acquire(board)` | Re-acquire port for MCP monitoring |

### Boot Analysis

| Tool | Description |
|---|---|
| `lab_boot_analyze(board)` | Analyze serial log: stage, errors, fixes, bootargs |

### Board Control

| Tool | Description |
|---|---|
| `lab_reboot(board, method)` | Reboot via serial/SSH/SysRq/relay |
| `lab_ssh_exec(board, command, timeout)` | Execute command on board via SSH |

### BSP Management

| Tool | Description |
|---|---|
| `lab_bsp_read(board, filename)` | Read BSP file (boot.cmd, config.txt) |
| `lab_bsp_write(board, filename, content)` | Write BSP file (.bak backup) |
| `lab_bsp_compile(board)` | Compile boot.cmd → boot.scr |
| `lab_bsp_deploy_sd(board)` | Deploy to mounted SD card |

### Build & Deploy

| Tool | Description |
|---|---|
| `lab_docker_exec(command, timeout)` | Run command in Docker (Tier 1) |
| `lab_tftp_list(subdir)` | List TFTP directory |
| `lab_nfs_list(board, path)` | List NFS rootfs |
| `lab_nfs_write(board, path, content, mode)` | Write to NFS rootfs |

### Bench Verification

| Tool | Description |
|---|---|
| `lab_bench_verify(board, success, fail, timeout)` | Reboot → wait → analyze |
| `lab_verify_report(board)` | Generate VERIFICATION_REPORT.md |

## Managing the Service

```bash
./lab mcp setup    # Create venv, install deps
./lab mcp start    # Enable & start systemd service
./lab mcp stop     # Stop the service
./lab mcp status   # Show status + port check
./lab mcp logs     # Tail journalctl logs
```

## Serial Port Sharing

The MCP server holds serial ports for background logging.  When you need
interactive console access:

1. Agent calls `lab_serial_release(board)` — port is freed
2. You run `picocom` or `minicom` for manual debugging
3. When done, agent calls `lab_serial_acquire(board)` — monitoring resumes

Gap periods are marked in the serial log.

## Adding a New Board

1. Create `shared/boards/<board>.env` with `BOARD_SERIAL_PORT` and `TARGET_IP`
2. Create `shared/bsp/<board>/` with boot files
3. Restart the MCP server: `./lab mcp stop && ./lab mcp start`

No code changes required — the server discovers boards from `.env` files.

## Troubleshooting

| Issue | Fix |
|---|---|
| `lab mcp setup` fails | Ensure `python3 -m venv` works (`apt install python3-venv`) |
| Service won't start | Check: `journalctl --user -u lab-mcp -n 50` |
| Port 8420 not listening | Verify service is active: `./lab mcp status` |
| Serial port busy | Another process holds the port. Kill `picocom`/`minicom` first |
| Agent can't connect | Set up SSH tunnel: `ssh -L 8420:localhost:8420 user@host` |
