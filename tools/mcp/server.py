#!/usr/bin/env python3
"""
server.py — ARM Embedded Linux Lab MCP Server (Hardware Tool Bridge)

Exposes 22 MCP tools over SSE transport (http://127.0.0.1:8420/sse) for
AI agent interaction with physical embedded Linux boards.  Implements the
Hardware Tool Bridge described in the Soliton Agentic FDLC blog.

Usage:
    python tools/mcp/server.py          # Start SSE server on port 8420
    python tools/mcp/server.py --stdio  # Use stdio transport (for debugging)
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import signal
import sys
from pathlib import Path
from typing import Optional

# Resolve repo root from this script's location (tools/mcp/server.py)
SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent.parent

# Import the pip-installed mcp package (FastMCP) — must happen before we add
# our own tools/mcp directory to sys.path, since both are named "mcp".
import importlib
_fastmcp_mod = importlib.import_module("mcp.server.fastmcp")
FastMCP = _fastmcp_mod.FastMCP

# Now import our local modules via direct path manipulation
sys.path.insert(0, str(SCRIPT_DIR))

import serial_manager as _serial_mod
import boot_analyzer as _boot_mod
import board_manager as _board_mod
import bsp_manager as _bsp_mod
import deploy_manager as _deploy_mod
import docker_bridge as _docker_mod
import bench_verifier as _bench_mod

SerialManager = _serial_mod.SerialManager
boot_analyze = _boot_mod.analyze
BoardManager = _board_mod.BoardManager
BSPManager = _bsp_mod.BSPManager
DeployManager = _deploy_mod.DeployManager
DockerBridge = _docker_mod.DockerBridge
BenchVerifier = _bench_mod.BenchVerifier

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("lab-mcp")

# ---------------------------------------------------------------------------
# MCP Server
# ---------------------------------------------------------------------------
MCP_HOST = "127.0.0.1"
MCP_PORT = 8420

mcp = FastMCP(
    "ARM Embedded Linux Lab",
    instructions=(
        "Hardware Tool Bridge for the ARM Embedded Linux Lab. "
        "Provides serial console access, boot log analysis, BSP management, "
        "board reboot, TFTP/NFS deployment, and bench verification."
    ),
    host=MCP_HOST,
    port=MCP_PORT,
)

# ---------------------------------------------------------------------------
# Manager singletons (initialized in main)
# ---------------------------------------------------------------------------
serial_mgr: SerialManager
board_mgr: BoardManager
bsp_mgr: BSPManager
deploy_mgr: DeployManager
docker_bridge: DockerBridge
bench_verifier: BenchVerifier


# ===========================================================================
# Board Discovery & Status (3 tools)
# ===========================================================================

@mcp.tool()
def lab_board_list() -> str:
    """List all configured boards with online/offline status.

    Returns a JSON array of boards with IP, serial port, and reachability.
    """
    boards = board_mgr.list_boards()
    return json.dumps(boards, indent=2)


@mcp.tool()
def lab_board_status(board: str) -> str:
    """Get detailed status for a specific board.

    Checks ping reachability, serial port presence, SSH connectivity,
    and reports the configured reset method.

    Args:
        board: Board name (e.g. "rpi4")
    """
    try:
        status = board_mgr.board_status(board)
        return json.dumps(status, indent=2)
    except ValueError as exc:
        return str(exc)


@mcp.tool()
def lab_doctor() -> str:
    """Run full lab diagnostics (toolchains, serial, TFTP, NFS).

    Executes ``./lab doctor`` inside the Docker container and returns
    the diagnostic output.
    """
    return board_mgr.run_doctor()


# ===========================================================================
# Serial Console — Trace Collection (5 tools)
# ===========================================================================

@mcp.tool()
def lab_serial_log(
    board: str,
    lines: int = 100,
    pattern: Optional[str] = None,
    since: Optional[str] = None,
) -> str:
    """Read serial output from a board's console.

    Returns recent serial log lines from the persistent ring buffer.
    Supports filtering by line count, regex pattern, or timestamp.

    Args:
        board: Board name (e.g. "rpi4")
        lines: Maximum number of lines to return (default: 100)
        pattern: Optional regex to filter lines (e.g. "panic|error")
        since: Optional ISO timestamp — only return lines after this time
    """
    try:
        entries = serial_mgr.get_log(board, lines=lines, pattern=pattern, since=since)
        return json.dumps(entries, indent=2)
    except ValueError as exc:
        return str(exc)


@mcp.tool()
def lab_serial_send(board: str, text: str) -> str:
    """Send a string to a board's serial port.

    Useful for sending U-Boot commands, pressing Enter, or sending Ctrl-C.
    Supports escape sequences: \\\\r (CR), \\\\n (LF), \\\\x03 (Ctrl-C).

    Args:
        board: Board name (e.g. "rpi4")
        text: Text to send (e.g. "reset\\\\r", "\\\\x03", "printenv\\\\r")
    """
    try:
        return serial_mgr.send(board, text)
    except ValueError as exc:
        return str(exc)


@mcp.tool()
async def lab_serial_wait(
    board: str,
    pattern: str,
    timeout_s: float = 30,
) -> str:
    """Wait for a regex pattern to appear in serial output.

    Blocks until the pattern is matched or the timeout expires.
    Returns the matching line if found, or a timeout indication.

    Args:
        board: Board name (e.g. "rpi4")
        pattern: Regex pattern to wait for (e.g. "login:|panic")
        timeout_s: Maximum seconds to wait (default: 30)
    """
    try:
        result = await serial_mgr.wait_for(board, pattern, timeout_s)
        return json.dumps(result, indent=2)
    except ValueError as exc:
        return str(exc)


@mcp.tool()
def lab_serial_release(board: str) -> str:
    """Release a board's serial port for manual picocom/minicom access.

    Stops the background reader thread and closes the port so the user
    can connect interactively.  Call lab_serial_acquire to resume monitoring.

    Args:
        board: Board name (e.g. "rpi4")
    """
    try:
        return serial_mgr.release(board)
    except ValueError as exc:
        return str(exc)


@mcp.tool()
def lab_serial_acquire(board: str) -> str:
    """Re-acquire a board's serial port for MCP monitoring.

    Reopens the serial port and restarts background log capture after
    a manual access session (picocom/minicom).

    Args:
        board: Board name (e.g. "rpi4")
    """
    try:
        return serial_mgr.acquire(board)
    except ValueError as exc:
        return str(exc)


# ===========================================================================
# Boot Log Analysis — Bench Feedback (1 tool)
# ===========================================================================

@mcp.tool()
def lab_boot_analyze(board: str) -> str:
    """Analyze the serial log buffer for boot issues.

    Scans the serial output using pattern matching to detect the current
    boot stage, classify errors (panic, NFS timeout, DTB overlap, etc.),
    and suggest fixes.  Each error includes a rule_suggestion for
    institutional knowledge capture.

    Args:
        board: Board name (e.g. "rpi4")
    """
    try:
        lines = serial_mgr.get_raw_lines(board)
        analysis = boot_analyze(lines)
        return json.dumps(analysis.to_dict(), indent=2)
    except ValueError as exc:
        return str(exc)


# ===========================================================================
# Board Control (2 tools)
# ===========================================================================

@mcp.tool()
def lab_reboot(board: str, method: Optional[str] = None) -> str:
    """Reboot a board via the specified method.

    Methods: uboot_serial (default), ssh, sysrq_serial, power_relay.
    Delegates to tools/target/reboot.sh.

    Args:
        board: Board name (e.g. "rpi4")
        method: Reboot method override (default: from board config)
    """
    try:
        return board_mgr.reboot(board, method)
    except ValueError as exc:
        return str(exc)


@mcp.tool()
def lab_ssh_exec(board: str, command: str, timeout: int = 30) -> str:
    """Execute a command on a board via SSH.

    Returns stdout, stderr, and exit code from the remote command.

    Args:
        board: Board name (e.g. "rpi4")
        command: Shell command to execute on the target
        timeout: Max seconds to wait (default: 30)
    """
    try:
        result = board_mgr.ssh_exec(board, command, timeout)
        return json.dumps(result, indent=2)
    except ValueError as exc:
        return str(exc)


# ===========================================================================
# BSP Management (4 tools)
# ===========================================================================

@mcp.tool()
def lab_bsp_read(board: str, filename: str) -> str:
    """Read a BSP file (boot.cmd, config.txt, cmdline.txt, etc.).

    Args:
        board: Board name (e.g. "rpi4")
        filename: File name within shared/bsp/{board}/ (e.g. "boot.cmd")
    """
    try:
        return bsp_mgr.read_file(board, filename)
    except ValueError as exc:
        return str(exc)


@mcp.tool()
def lab_bsp_write(board: str, filename: str, content: str) -> str:
    """Write content to a BSP file (creates .bak backup first).

    Args:
        board: Board name (e.g. "rpi4")
        filename: File name within shared/bsp/{board}/ (e.g. "boot.cmd")
        content: New file content
    """
    try:
        return bsp_mgr.write_file(board, filename, content)
    except ValueError as exc:
        return str(exc)


@mcp.tool()
def lab_bsp_compile(board: str) -> str:
    """Compile boot.cmd into boot.scr via mkimage.

    Requires mkimage to be installed on the host (or run inside Docker).

    Args:
        board: Board name (e.g. "rpi4")
    """
    try:
        return bsp_mgr.compile_bootscr(board)
    except ValueError as exc:
        return str(exc)


@mcp.tool()
def lab_bsp_deploy_sd(board: str) -> str:
    """Deploy boot artifacts to a mounted SD card.

    Wraps tools/target/deploy_bootfs.sh.  The SD card must be mounted
    at /media/$USER/BOOT or /media/$USER/bootfs.

    Args:
        board: Board name (e.g. "rpi4")
    """
    try:
        return bsp_mgr.deploy_sd(board)
    except ValueError as exc:
        return str(exc)


# ===========================================================================
# Build & Deploy — Tiered Verification (4 tools)
# ===========================================================================

@mcp.tool()
def lab_docker_exec(command: str, timeout: int = 120) -> str:
    """Run a command inside the Docker development container (Tier 1).

    Use for cross-compilation, host-side unit tests, kernel builds, etc.
    The container must be running (start with: ./lab docker).

    Args:
        command: Shell command to execute inside the container
        timeout: Max seconds to wait (default: 120)
    """
    result = docker_bridge.exec(command, timeout)
    return json.dumps(result, indent=2)


@mcp.tool()
def lab_tftp_list(subdir: Optional[str] = None) -> str:
    """List files in the TFTP serving directory.

    Args:
        subdir: Optional subdirectory within tftp/ to list
    """
    try:
        entries = deploy_mgr.tftp_list(subdir)
        return json.dumps(entries, indent=2)
    except ValueError as exc:
        return str(exc)


@mcp.tool()
def lab_nfs_list(board: str, path: str = "/") -> str:
    """List contents of the NFS rootfs for a board.

    Args:
        board: Board name (e.g. "rpi4")
        path: Relative path within the rootfs (default: root "/")
    """
    try:
        entries = deploy_mgr.nfs_list(board, path)
        return json.dumps(entries, indent=2)
    except ValueError as exc:
        return str(exc)


@mcp.tool()
def lab_nfs_write(
    board: str,
    path: str,
    content: str,
    mode: str = "644",
) -> str:
    """Write a file to the NFS rootfs.

    Args:
        board: Board name (e.g. "rpi4")
        path: File path relative to rootfs root (e.g. "etc/init.d/rcS")
        content: File content to write
        mode: Octal permission string (default: "644")
    """
    try:
        return deploy_mgr.nfs_write(board, path, content, mode)
    except ValueError as exc:
        return str(exc)


# ===========================================================================
# Bench Verification — Closing the Loop (2 tools)
# ===========================================================================

@mcp.tool()
async def lab_bench_verify(
    board: str,
    success_pattern: str = "login:",
    fail_patterns: Optional[str] = None,
    timeout_s: int = 90,
    reboot_method: Optional[str] = None,
) -> str:
    """Run a scripted bench verification: reboot → wait → analyze → report.

    Implements the Agentic FDLC Tier 2 bench verification workflow.
    Returns a structured pass/fail result with boot analysis.

    Args:
        board: Board name (e.g. "rpi4")
        success_pattern: Regex for successful boot (default: "login:")
        fail_patterns: Comma-separated failure regexes (default: "Kernel panic,Unable to mount root")
        timeout_s: Max seconds to wait for boot (default: 90)
        reboot_method: Override reboot method (default: from board config)
    """
    fp = (
        fail_patterns.split(",")
        if fail_patterns
        else ["Kernel panic", "Unable to mount root"]
    )
    try:
        result = await bench_verifier.verify(
            board=board,
            success_pattern=success_pattern,
            fail_patterns=fp,
            timeout_s=timeout_s,
            reboot_method=reboot_method,
        )
        return json.dumps(result, indent=2)
    except ValueError as exc:
        return str(exc)


@mcp.tool()
def lab_verify_report(board: str) -> str:
    """Generate VERIFICATION_REPORT.md from the last bench verification.

    Writes the report to the repo root and returns its Markdown content.

    Args:
        board: Board name (e.g. "rpi4")
    """
    return bench_verifier.generate_report(board)


# ===========================================================================
# Server lifecycle
# ===========================================================================

def _init_managers() -> None:
    """Initialize all manager singletons."""
    global serial_mgr, board_mgr, bsp_mgr, deploy_mgr, docker_bridge, bench_verifier

    boards_dir = REPO_ROOT / "shared" / "boards"
    log_dir = SCRIPT_DIR / "logs"

    serial_mgr = SerialManager(boards_dir, log_dir)
    board_mgr = BoardManager(REPO_ROOT)
    bsp_mgr = BSPManager(REPO_ROOT)
    deploy_mgr = DeployManager(REPO_ROOT)
    docker_bridge = DockerBridge(REPO_ROOT)
    bench_verifier = BenchVerifier(serial_mgr, board_mgr, REPO_ROOT)

    # Start serial monitoring
    serial_mgr.start_all()
    logger.info("Serial monitoring started for boards: %s",
                ", ".join(serial_mgr.boards_with_serial()) or "(none)")


def _shutdown(signum, frame) -> None:
    """Graceful shutdown handler."""
    logger.info("Shutting down (signal %s)...", signum)
    serial_mgr.stop_all()
    sys.exit(0)


def main() -> None:
    _init_managers()

    signal.signal(signal.SIGTERM, _shutdown)
    signal.signal(signal.SIGINT, _shutdown)

    if "--stdio" in sys.argv:
        transport = "stdio"
        logger.info("Starting MCP server (stdio transport)")
    else:
        transport = "sse"
        logger.info("Starting MCP server on http://%s:%d/sse", MCP_HOST, MCP_PORT)

    try:
        mcp.run(transport=transport)
    finally:
        serial_mgr.stop_all()


if __name__ == "__main__":
    main()
