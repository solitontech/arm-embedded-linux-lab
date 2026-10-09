"""
deploy_manager.py — TFTP and NFS rootfs file management.

Provides directory listing and file write operations for the TFTP serving
directory and per-board NFS root filesystems.  Path validation prevents
directory-escape attacks.
"""

from __future__ import annotations

import logging
import os
import stat
from pathlib import Path
from typing import Optional

logger = logging.getLogger("lab-mcp.deploy")


class DeployManager:
    """Manage TFTP directory and NFS rootfs contents."""

    def __init__(self, repo_root: Path):
        self._repo = repo_root
        self._tftp_dir = repo_root / "tftp"
        self._nfs_dir = repo_root / "nfs"

    # -- TFTP -------------------------------------------------------------

    def tftp_list(self, subdir: Optional[str] = None) -> list[dict]:
        """List files in the TFTP directory.

        Args:
            subdir: optional subdirectory within tftp/
        """
        target = self._tftp_dir
        if subdir:
            target = self._safe_resolve(self._tftp_dir, subdir)

        if not target.is_dir():
            return [{"error": f"TFTP directory {target} does not exist"}]

        entries = []
        for item in sorted(target.iterdir()):
            entries.append(
                {
                    "name": item.name,
                    "type": "dir" if item.is_dir() else "file",
                    "size": item.stat().st_size if item.is_file() else 0,
                }
            )
        return entries

    # -- NFS rootfs -------------------------------------------------------

    def nfs_list(self, board: str, path: str = "/") -> list[dict]:
        """List contents of the NFS rootfs for a board.

        Args:
            board: board name (e.g. "rpi4" -> nfs/rpi4-rootfs/)
            path: relative path within the rootfs (default: root)
        """
        rootfs = self._nfs_rootfs(board)
        target = self._safe_resolve(rootfs, path.lstrip("/"))

        if not target.is_dir():
            return [{"error": f"{target} does not exist or is not a directory"}]

        entries = []
        for item in sorted(target.iterdir()):
            entries.append(
                {
                    "name": item.name,
                    "type": "dir" if item.is_dir() else "file",
                    "size": item.stat().st_size if item.is_file() else 0,
                }
            )
        return entries

    def nfs_write(
        self,
        board: str,
        path: str,
        content: str,
        mode: str = "644",
    ) -> str:
        """Write a file to the NFS rootfs.

        Args:
            board: board name
            path: file path relative to rootfs root (e.g. "etc/init.d/rcS")
            content: file content
            mode: octal permission string (default "644")
        """
        rootfs = self._nfs_rootfs(board)
        target = self._safe_resolve(rootfs, path.lstrip("/"))

        # Create parent directories
        target.parent.mkdir(parents=True, exist_ok=True)

        target.write_text(content, encoding="utf-8")
        os.chmod(target, int(mode, 8))
        logger.info("Wrote %d bytes to %s (mode %s)", len(content), target, mode)
        return f"Wrote {len(content)} bytes to nfs/{board}-rootfs/{path} (mode {mode})"

    # -- internal ---------------------------------------------------------

    def _nfs_rootfs(self, board: str) -> Path:
        rootfs = self._nfs_dir / f"{board}-rootfs"
        if not rootfs.is_dir():
            available = sorted(
                d.name
                for d in self._nfs_dir.iterdir()
                if d.is_dir() and d.name.endswith("-rootfs")
            ) if self._nfs_dir.is_dir() else []
            raise ValueError(
                f"NFS rootfs for '{board}' not found at {rootfs}. "
                f"Available: {', '.join(available) or '(none)'}"
            )
        return rootfs

    def _safe_resolve(self, base: Path, relative: str) -> Path:
        """Resolve a relative path under base, preventing directory escape."""
        # Normalize and reject absolute or parent traversal
        normalized = os.path.normpath(relative)
        if normalized.startswith("..") or normalized.startswith("/"):
            raise ValueError(f"Path escape attempt: {relative}")
        resolved = (base / normalized).resolve()
        if not str(resolved).startswith(str(base.resolve())):
            raise ValueError(f"Path escape attempt: {relative}")
        return resolved
