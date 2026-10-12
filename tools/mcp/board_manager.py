"""
board_manager.py — Board discovery, status, reboot, and SSH execution.

Scans ``shared/boards/*.env`` for board profiles and provides ping/SSH
reachability checks, reboot dispatch (via tools/target/reboot.sh), and
remote command execution over SSH.
"""

from __future__ import annotations

import logging
import os
import shutil
import socket
import subprocess
from pathlib import Path
from typing import Optional

logger = logging.getLogger("lab-mcp.board")


class BoardManager:
    """Manage board discovery, status, and control operations."""

    def __init__(self, repo_root: Path):
        self._repo = repo_root
        self._boards_dir = repo_root / "shared" / "boards"

    # -- discovery --------------------------------------------------------

    def list_boards(self) -> list[dict]:
        """Return all configured boards with basic info and online status."""
        boards = []
        for env_file in sorted(self._boards_dir.glob("*.env")):
            if env_file.name.endswith(".example"):
                continue
            board = env_file.stem
            cfg = self._parse_env(env_file)
            ip = cfg.get("TARGET_IP", "")
            online = self._ping(ip) if ip else False
            boards.append(
                {
                    "board": board,
                    "ip": ip,
                    "online": online,
                    "serial_port": cfg.get("BOARD_SERIAL_PORT", ""),
                    "user": cfg.get("TARGET_USER", "root"),
                }
            )
        return boards

    def board_status(self, board: str) -> dict:
        """Detailed status: ping, serial device, SSH reachability."""
        cfg = self._load_board(board)
        ip = cfg.get("TARGET_IP", "")
        serial_port = cfg.get("BOARD_SERIAL_PORT", "")
        ssh_port = int(cfg.get("TARGET_PORT", "22"))

        ping_ok = self._ping(ip) if ip else False
        serial_exists = os.path.exists(serial_port) if serial_port else False
        ssh_ok = False
        if ping_ok:
            ssh_ok = self._check_tcp(ip, ssh_port)

        return {
            "board": board,
            "ip": ip,
            "ping": ping_ok,
            "serial_port": serial_port,
            "serial_exists": serial_exists,
            "ssh_reachable": ssh_ok,
            "ssh_port": ssh_port,
            "user": cfg.get("TARGET_USER", "root"),
            "reset_method": cfg.get("BOARD_RESET_METHOD", "uboot_serial"),
        }

    # -- serial manager reference (set by server.py after init) ----------
    _serial_mgr: Optional[object] = None

    def set_serial_manager(self, serial_mgr) -> None:
        """Inject the SerialManager so reboot can use the live serial port."""
        self._serial_mgr = serial_mgr

    # -- reboot -----------------------------------------------------------

    def reboot(self, board: str, method: Optional[str] = None) -> str:
        """Reboot a board via the specified method.

        Serial-based methods (uboot_serial, sysrq_serial) use the MCP
        server's own serial connection to avoid port conflicts.  SSH and
        power_relay methods delegate to tools/target/reboot.sh.
        """
        cfg = self._load_board(board)
        method = method or cfg.get("BOARD_RESET_METHOD", "uboot_serial")

        if method in ("uboot_serial", "serial"):
            return self._reboot_uboot_serial(board, cfg)
        elif method in ("sysrq_serial", "sysrq"):
            return self._reboot_sysrq(board, cfg)
        elif method == "ssh":
            return self._reboot_ssh(board, cfg)
        elif method in ("power_relay", "relay"):
            return self._reboot_via_script(board, cfg, method)
        else:
            return f"ERROR: Unknown reboot method '{method}'. Supported: uboot_serial, ssh, sysrq_serial, power_relay"

    def _reboot_uboot_serial(self, board: str, cfg: dict) -> str:
        """Send reset command over the MCP-held serial port."""
        if not self._serial_mgr:
            return "ERROR: SerialManager not available"

        reset_cmd = cfg.get("BOARD_RESET_CMD", "reset\\r")
        # Send Enter first to get to a clean prompt, then the reset command
        try:
            self._serial_mgr.send(board, "\\r")
            import time
            time.sleep(0.2)
            self._serial_mgr.send(board, reset_cmd)
            return f"U-Boot reset command sent to {board} via serial"
        except ValueError as exc:
            return f"ERROR: {exc}"

    def _reboot_sysrq(self, board: str, cfg: dict) -> str:
        """Send Magic SysRq Break+b over the MCP-held serial port."""
        if not self._serial_mgr:
            return "ERROR: SerialManager not available"

        try:
            bs = self._serial_mgr._get_board(board)
            if bs._released:
                return f"ERROR: serial port for {board} is released. Call lab_serial_acquire first."
            if not bs.ser or not bs.ser.is_open:
                return f"ERROR: serial port for {board} is not open"
            bs.ser.send_break(duration=0.25)
            import time
            time.sleep(0.1)
            bs.ser.write(b"b")
            bs._append_line(">>> SENT: SysRq Break+b (reboot)")
            return f"Magic SysRq reboot sent to {board} via serial"
        except ValueError as exc:
            return f"ERROR: {exc}"

    def _reboot_ssh(self, board: str, cfg: dict) -> str:
        """Reboot via SSH."""
        ip = cfg.get("TARGET_IP", "")
        if not ip:
            return f"ERROR: TARGET_IP not configured for {board}"
        result = self.ssh_exec(board, "nohup reboot >/dev/null 2>&1 &", timeout=10)
        if "error" in result:
            return f"SSH reboot failed: {result['error']}"
        return f"SSH reboot command sent to {board} ({ip})"

    def _reboot_via_script(self, board: str, cfg: dict, method: str) -> str:
        """Delegate to tools/target/reboot.sh for methods that need it."""
        reboot_script = self._repo / "tools" / "target" / "reboot.sh"
        if not reboot_script.exists():
            return f"ERROR: reboot script not found at {reboot_script}"
        cmd = [
            str(reboot_script),
            f"--board={board}",
            f"--method={method}",
            f"--serial-port={cfg.get('BOARD_SERIAL_PORT', '')}",
            f"--serial-baud={cfg.get('BOARD_SERIAL_BAUD', '115200')}",
            f"--target-ip={cfg.get('TARGET_IP', '')}",
            f"--target-user={cfg.get('TARGET_USER', 'root')}",
        ]
        try:
            res = subprocess.run(
                cmd, capture_output=True, text=True, timeout=15,
            )
            output = (res.stdout + res.stderr).strip()
            if res.returncode == 0:
                return f"Reboot triggered for {board} via {method}.\n{output}"
            return f"Reboot failed (exit {res.returncode}):\n{output}"
        except subprocess.TimeoutExpired:
            return f"Reboot command timed out for {board}"
        except Exception as exc:
            return f"Reboot error: {exc}"

    # -- SSH exec ---------------------------------------------------------

    def ssh_exec(
        self, board: str, command: str, timeout: int = 30
    ) -> dict:
        """Execute a command on the board via SSH and return output."""
        cfg = self._load_board(board)
        ip = cfg.get("TARGET_IP", "")
        user = cfg.get("TARGET_USER", "root")
        port = cfg.get("TARGET_PORT", "22")
        ssh_key = cfg.get("TARGET_SSH_KEY", "")

        if not ip:
            return {"error": f"TARGET_IP not configured for {board}"}

        ssh_cmd = [
            "ssh",
            "-o", "StrictHostKeyChecking=no",
            "-o", "UserKnownHostsFile=/dev/null",
            "-o", f"ConnectTimeout={min(timeout, 10)}",
            "-p", port,
        ]
        if ssh_key:
            key_path = os.path.expanduser(ssh_key)
            if os.path.exists(key_path):
                ssh_cmd.extend(["-i", key_path])
        ssh_cmd.append(f"{user}@{ip}")
        ssh_cmd.append(command)

        try:
            res = subprocess.run(
                ssh_cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            return {
                "exit_code": res.returncode,
                "stdout": res.stdout,
                "stderr": res.stderr,
            }
        except subprocess.TimeoutExpired:
            return {"error": f"SSH command timed out after {timeout}s"}
        except Exception as exc:
            return {"error": str(exc)}

    # -- doctor -----------------------------------------------------------

    def run_doctor(self) -> str:
        """Run ``./lab doctor`` inside Docker and return output."""
        docker_script = self._repo / "tools" / "docker" / "run.sh"
        if not docker_script.exists():
            return "ERROR: tools/docker/run.sh not found"
        try:
            res = subprocess.run(
                [str(docker_script), "exec", "./lab", "doctor"],
                capture_output=True,
                text=True,
                timeout=60,
                cwd=str(self._repo),
            )
            return (res.stdout + res.stderr).strip()
        except subprocess.TimeoutExpired:
            return "ERROR: lab doctor timed out after 60s"
        except Exception as exc:
            return f"ERROR: {exc}"

    # -- internal ---------------------------------------------------------

    def _load_board(self, board: str) -> dict[str, str]:
        env_file = self._boards_dir / f"{board}.env"
        if not env_file.exists():
            available = [
                f.stem
                for f in self._boards_dir.glob("*.env")
                if not f.name.endswith(".example")
            ]
            raise ValueError(
                f"Board '{board}' not found. Available: {', '.join(available) or '(none)'}"
            )
        return self._parse_env(env_file)

    @staticmethod
    def _ping(ip: str, timeout: int = 1) -> bool:
        if not ip or ip == "127.0.0.1":
            return False
        try:
            return (
                subprocess.call(
                    ["ping", "-c", "1", "-W", str(timeout), ip],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                == 0
            )
        except Exception:
            return False

    @staticmethod
    def _check_tcp(ip: str, port: int, timeout: float = 2.0) -> bool:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(timeout)
            s.connect((ip, port))
            s.close()
            return True
        except Exception:
            return False

    @staticmethod
    def _parse_env(path: Path) -> dict[str, str]:
        result: dict[str, str] = {}
        for line in path.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            key, _, val = line.partition("=")
            result[key.strip()] = val.strip().strip('"').strip("'")
        return result
