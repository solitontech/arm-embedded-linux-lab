---
description: Set up and configure the MCP Hardware Tool Bridge server on a Linux host machine.
---

# MCP Server Setup Workflow

## When to Use This Workflow

Use this workflow when setting up the MCP server (Hardware Tool Bridge) on a new
Linux host machine, or when reconfiguring it after a repo move or hardware change.

## Prerequisites

- Native Linux host (not WSL2) with Python 3.10+
- USB-to-serial adapter connected to the board
- Board configured in `shared/boards/<board>.env` with `BOARD_SERIAL_PORT`
- Docker installed (for `lab_docker_exec` and `lab_doctor` tools)

## Steps

1. **Install the MCP server virtual environment**
   ```bash
   ./lab mcp setup
   ```
   This creates `tools/mcp/venv/` and installs `mcp[cli]` and `pyserial`.

2. **Verify board serial configuration**
   Ensure `shared/boards/<board>.env` has the correct serial port:
   ```bash
   cat shared/boards/rpi4.env | grep BOARD_SERIAL
   # BOARD_SERIAL_PORT="/dev/ttyUSB0"
   # BOARD_SERIAL_BAUD="115200"
   ```

3. **Start the MCP server**
   ```bash
   ./lab mcp start
   ```
   This links and enables the systemd user service `lab-mcp`.

4. **Verify the server is running**
   ```bash
   ./lab mcp status
   ```
   Expected output: service active, port 8420 listening.

5. **Configure AI agent MCP connection**

   For **local** agents (running on the same host):
   The `.devin/config.json` in the repo is pre-configured.

   For **remote** agents (e.g. Devin on Windows connecting via SSH):
   Set up an SSH tunnel:
   ```bash
   ssh -L 8420:localhost:8420 user@linux-host
   ```
   Then configure the agent's MCP settings:
   ```json
   {
     "mcpServers": {
       "lab": {
         "serverUrl": "http://localhost:8420/sse"
       }
     }
   }
   ```

6. **Test the connection**
   Use the agent to call `lab_board_list()` and verify it returns the
   configured boards.

## Files Touched

- `[CREATE]` `tools/mcp/venv/` (virtual environment, gitignored)
- `[READ]` `shared/boards/*.env` (board serial config)
- `[READ]` `.devin/config.json` (MCP client config)
- `[READ]` `tools/mcp/lab-mcp.service` (systemd unit)

## Notes

- The server binds to 127.0.0.1 only — no network exposure without SSH tunnel.
- Serial logs persist in `tools/mcp/logs/` across restarts.
- To add a new board, create its `.env` file and restart the server.
- If the serial port path changes (e.g. different USB port), update the `.env` and restart.
- The systemd service file uses `%h` (home directory) — if the repo moves, re-run `./lab mcp start`.
