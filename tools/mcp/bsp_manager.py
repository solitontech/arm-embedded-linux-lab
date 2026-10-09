"""
bsp_manager.py — BSP file read/write, boot.scr compilation, and SD card deploy.

Operates on ``shared/bsp/{board}/`` files (boot.cmd, config.txt, cmdline.txt,
DTBs, firmware blobs).  Write operations create a ``.bak`` backup before
overwriting.
"""

from __future__ import annotations

import logging
import shutil
import subprocess
from pathlib import Path
from typing import Optional

logger = logging.getLogger("lab-mcp.bsp")


class BSPManager:
    """Manage Board Support Package files."""

    def __init__(self, repo_root: Path):
        self._repo = repo_root
        self._bsp_dir = repo_root / "shared" / "bsp"

    # -- read / list ------------------------------------------------------

    def list_files(self, board: str) -> list[str]:
        """List all files in the BSP directory for a board."""
        bsp = self._board_dir(board)
        return sorted(f.name for f in bsp.iterdir() if f.is_file())

    def read_file(self, board: str, filename: str) -> str:
        """Read the contents of a BSP file."""
        path = self._resolve(board, filename)
        return path.read_text(encoding="utf-8", errors="replace")

    # -- write ------------------------------------------------------------

    def write_file(self, board: str, filename: str, content: str) -> str:
        """Write content to a BSP file (creates .bak backup first)."""
        path = self._resolve_writable(board, filename)
        # backup
        if path.exists():
            bak = path.with_suffix(path.suffix + ".bak")
            shutil.copy2(path, bak)
            logger.info("Backed up %s -> %s", path, bak)
        path.write_text(content, encoding="utf-8")
        logger.info("Wrote %d bytes to %s", len(content), path)
        return f"Wrote {len(content)} bytes to {path.relative_to(self._repo)}"

    # -- compile boot.scr ------------------------------------------------

    def compile_bootscr(self, board: str) -> str:
        """Compile boot.cmd -> boot.scr via mkimage."""
        bsp = self._board_dir(board)
        boot_cmd = bsp / "boot.cmd"
        boot_scr = bsp / "boot.scr"

        if not boot_cmd.exists():
            return f"ERROR: {boot_cmd.relative_to(self._repo)} does not exist"

        if not shutil.which("mkimage"):
            return (
                "ERROR: mkimage not found. Install u-boot-tools or run "
                "inside Docker: mkimage -C none -A arm64 -T script -d "
                f"shared/bsp/{board}/boot.cmd shared/bsp/{board}/boot.scr"
            )

        try:
            res = subprocess.run(
                [
                    "mkimage",
                    "-C", "none",
                    "-A", "arm64",
                    "-T", "script",
                    "-d", str(boot_cmd),
                    str(boot_scr),
                ],
                capture_output=True,
                text=True,
                timeout=15,
            )
            if res.returncode == 0:
                return f"Compiled boot.scr for {board}\n{res.stdout.strip()}"
            return f"mkimage failed (exit {res.returncode}):\n{res.stderr.strip()}"
        except subprocess.TimeoutExpired:
            return "ERROR: mkimage timed out"
        except Exception as exc:
            return f"ERROR: {exc}"

    # -- deploy to SD card ------------------------------------------------

    def deploy_sd(self, board: str) -> str:
        """Deploy boot artifacts to a mounted SD card.

        Wraps tools/target/deploy_bootfs.sh.
        """
        deploy_script = self._repo / "tools" / "target" / "deploy_bootfs.sh"
        if not deploy_script.exists():
            return f"ERROR: {deploy_script.relative_to(self._repo)} not found"

        try:
            res = subprocess.run(
                [str(deploy_script), board],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=str(self._repo),
            )
            output = (res.stdout + res.stderr).strip()
            if res.returncode == 0:
                return f"SD card deploy complete for {board}.\n{output}"
            return f"SD card deploy failed (exit {res.returncode}):\n{output}"
        except subprocess.TimeoutExpired:
            return "ERROR: SD card deploy timed out"
        except Exception as exc:
            return f"ERROR: {exc}"

    # -- internal ---------------------------------------------------------

    def _board_dir(self, board: str) -> Path:
        d = self._bsp_dir / board
        if not d.is_dir():
            available = sorted(
                p.name for p in self._bsp_dir.iterdir() if p.is_dir()
            )
            raise ValueError(
                f"BSP directory for '{board}' not found. "
                f"Available: {', '.join(available) or '(none)'}"
            )
        return d

    def _resolve(self, board: str, filename: str) -> Path:
        path = self._board_dir(board) / filename
        if not path.exists():
            available = self.list_files(board)
            raise ValueError(
                f"File '{filename}' not found in shared/bsp/{board}/. "
                f"Available: {', '.join(available)}"
            )
        return path

    def _resolve_writable(self, board: str, filename: str) -> Path:
        bsp = self._board_dir(board)
        # Allow writing to existing files or creating new ones in BSP dir
        return bsp / filename
