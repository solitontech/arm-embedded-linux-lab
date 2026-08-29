---
description: how to add a new hardware board profile to the monorepo
---

# Add a New Board Profile

## When to Use This Workflow
Use this workflow when adding support for a new hardware controller (e.g., Raspberry Pi 3, BeagleBone Black) that will be physically connected to the Ubuntu lab host.

## Prerequisites
- The board is physically connected to the Ubuntu lab host via a USB-to-Serial cable
- You know the board's serial port device (e.g., `/dev/ttyUSB1`) and baud rate

## Steps

1. **Create the board profile from the example**
   ```bash
   cp tools/deploy/boards/rpi4.env.example tools/deploy/boards/<board-name>.env
   ```

2. **Fill in the board-specific values**
   Edit `tools/deploy/boards/<board-name>.env`:
   - `BOARD_SERIAL_PORT` — the `/dev/ttyUSBx` device on the Ubuntu host
   - `BOARD_SERIAL_BAUD` — typically `115200`
   - `BOARD_RESET_CMD` — U-Boot reset command (usually `reset\r`)

3. **Create a committed example file**
   Copy the filled-in values (with placeholder substitutions) to an `.env.example`:
   ```bash
   cp tools/deploy/boards/<board-name>.env tools/deploy/boards/<board-name>.env.example
   # Then replace real values with placeholders in the .example file
   ```

4. **Verify the serial connection**
   From the Ubuntu lab host:
   ```bash
   picocom -b 115200 /dev/ttyUSB<N>
   ```
   You should see the board's boot output.

5. **Test the deployment script**
   ```bash
   ./tools/deploy/trigger_tftp_boot.sh --board=<board-name>
   ```

## Files Touched
- `[CREATE]` `tools/deploy/boards/<board-name>.env` (git-ignored, stays local)
- `[CREATE]` `tools/deploy/boards/<board-name>.env.example` (committed to repo)

## Notes
- The `*.env` files are listed in `.gitignore` — never commit them as they contain real lab IP addresses.
- Only the `*.env.example` counterpart should be committed.
