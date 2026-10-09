"""
serial_manager.py — Serial port background capture, ring buffer, and disk persistence.

Each configured board gets a dedicated reader thread that continuously captures
serial output into an in-memory ring buffer and appends it to a disk log file.
Agents query the buffer via get_log() and can wait for specific patterns via
wait_for().  The release()/acquire() mechanism allows the user to reclaim the
serial port for interactive picocom/minicom access without killing the server.
"""

from __future__ import annotations

import asyncio
import collections
import logging
import os
import re
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

try:
    import serial  # pyserial
except ImportError:
    serial = None  # type: ignore[assignment]

logger = logging.getLogger("lab-mcp.serial")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
RING_BUFFER_MAX = 20_000
DISK_TAIL_ON_STARTUP = 2_000
RETRY_INTERVAL_S = 30
READLINE_TIMEOUT_S = 1.0


# ---------------------------------------------------------------------------
# Per-board serial state
# ---------------------------------------------------------------------------
class _BoardSerial:
    """Internal state for one board's serial connection."""

    def __init__(self, board: str, port: str, baud: int, log_dir: Path):
        self.board = board
        self.port = port
        self.baud = baud
        self.log_file = log_dir / f"{board}_serial.log"

        # Ring buffer: deque of (iso_timestamp, line_text)
        self.buffer: collections.deque[tuple[str, str]] = collections.deque(
            maxlen=RING_BUFFER_MAX
        )
        self.lock = threading.Lock()

        # Serial handle (None when released or not yet connected)
        self.ser: Optional[serial.Serial] = None  # type: ignore[name-defined]

        # Reader thread management
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._released = False

        # Pattern waiters: list of (compiled_re, asyncio.Event, result_holder_list, loop)
        self._waiters: list[
            tuple[re.Pattern, asyncio.Event, list, asyncio.AbstractEventLoop]
        ] = []
        self._waiter_lock = threading.Lock()

    # -- helpers ----------------------------------------------------------

    def _append_line(self, line: str) -> None:
        ts = datetime.now(timezone.utc).isoformat(timespec="milliseconds")
        with self.lock:
            self.buffer.append((ts, line))
        # disk persistence (append)
        try:
            with open(self.log_file, "a", encoding="utf-8", errors="replace") as fh:
                fh.write(f"{ts}\t{line}\n")
        except OSError:
            pass
        # notify waiters
        self._check_waiters(ts, line)

    def _check_waiters(self, ts: str, line: str) -> None:
        with self._waiter_lock:
            remaining = []
            for pat, evt, holder, loop in self._waiters:
                if pat.search(line):
                    holder.append((ts, line))
                    loop.call_soon_threadsafe(evt.set)
                else:
                    remaining.append((pat, evt, holder, loop))
            self._waiters = remaining

    # -- reader thread ----------------------------------------------------

    def _reader_loop(self) -> None:
        """Background thread: open serial port and read lines forever."""
        while not self._stop_event.is_set():
            try:
                if serial is None:
                    logger.error("pyserial is not installed")
                    return
                self.ser = serial.Serial(
                    self.port,
                    self.baud,
                    timeout=READLINE_TIMEOUT_S,
                )
                logger.info("Opened %s for board %s", self.port, self.board)
                self._append_line(f"--- serial acquired ({self.port} @ {self.baud}) ---")

                while not self._stop_event.is_set():
                    raw = self.ser.readline()
                    if raw:
                        line = raw.decode("utf-8", errors="replace").rstrip("\r\n")
                        self._append_line(line)
            except serial.SerialException as exc:
                logger.warning(
                    "Serial %s (%s) error: %s — retrying in %ds",
                    self.port,
                    self.board,
                    exc,
                    RETRY_INTERVAL_S,
                )
                self._close_port()
                self._stop_event.wait(RETRY_INTERVAL_S)
            except Exception:
                logger.exception("Unexpected error in serial reader for %s", self.board)
                self._close_port()
                self._stop_event.wait(RETRY_INTERVAL_S)

    def _close_port(self) -> None:
        if self.ser and self.ser.is_open:
            try:
                self.ser.close()
            except Exception:
                pass
        self.ser = None

    # -- public API -------------------------------------------------------

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._released = False
        self._thread = threading.Thread(
            target=self._reader_loop, daemon=True, name=f"serial-{self.board}"
        )
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        self._close_port()
        if self._thread:
            self._thread.join(timeout=5)
        self._thread = None

    def release(self) -> str:
        """Release serial port for manual access."""
        if self._released:
            return f"{self.board}: already released"
        self.stop()
        self._released = True
        self._append_line("--- serial released for manual access ---")
        return f"{self.board}: serial port {self.port} released"

    def acquire(self) -> str:
        """Re-acquire serial port for MCP monitoring."""
        if not self._released:
            return f"{self.board}: already acquired"
        self._released = False
        self.start()
        return f"{self.board}: serial port {self.port} re-acquired"


# ---------------------------------------------------------------------------
# Public manager
# ---------------------------------------------------------------------------
class SerialManager:
    """Manages serial connections for all configured boards."""

    def __init__(self, boards_dir: Path, log_dir: Path):
        self._boards_dir = boards_dir
        self._log_dir = log_dir
        self._log_dir.mkdir(parents=True, exist_ok=True)
        self._board_serials: dict[str, _BoardSerial] = {}

    # -- lifecycle --------------------------------------------------------

    def start_all(self) -> None:
        """Discover boards from .env files and start serial readers."""
        for env_file in sorted(self._boards_dir.glob("*.env")):
            if env_file.name.endswith(".example"):
                continue
            board = env_file.stem
            cfg = self._parse_env(env_file)
            port = cfg.get("BOARD_SERIAL_PORT", "")
            baud = int(cfg.get("BOARD_SERIAL_BAUD", "115200"))
            if not port:
                logger.info("Board %s has no BOARD_SERIAL_PORT — skipping serial", board)
                continue
            bs = _BoardSerial(board, port, baud, self._log_dir)
            self._load_history(bs)
            self._board_serials[board] = bs
            bs.start()
            logger.info("Started serial monitor for %s on %s", board, port)

    def stop_all(self) -> None:
        for bs in self._board_serials.values():
            bs.stop()

    # -- query API --------------------------------------------------------

    def boards_with_serial(self) -> list[str]:
        return list(self._board_serials.keys())

    def get_log(
        self,
        board: str,
        lines: int = 100,
        pattern: Optional[str] = None,
        since: Optional[str] = None,
    ) -> list[dict]:
        """Return recent serial log lines.

        Args:
            board: board name
            lines: max lines to return
            pattern: optional regex to filter lines
            since: optional ISO timestamp — only return lines after this
        """
        bs = self._get_board(board)
        compiled = re.compile(pattern) if pattern else None
        with bs.lock:
            entries = list(bs.buffer)
        result: list[dict] = []
        for ts, text in entries:
            if since and ts < since:
                continue
            if compiled and not compiled.search(text):
                continue
            result.append({"timestamp": ts, "line": text})
        return result[-lines:]

    def send(self, board: str, text: str) -> str:
        """Send text over serial.  Supports \\r, \\n, \\x03 (Ctrl-C) escapes."""
        bs = self._get_board(board)
        if bs._released:
            return f"ERROR: serial port for {board} is released for manual access. Call lab_serial_acquire first."
        if not bs.ser or not bs.ser.is_open:
            return f"ERROR: serial port for {board} is not open (device may be unplugged)"
        decoded = (
            text.replace("\\r", "\r")
            .replace("\\n", "\n")
            .replace("\\x03", "\x03")
        )
        bs.ser.write(decoded.encode("utf-8"))
        bs._append_line(f">>> SENT: {text}")
        return f"Sent {len(decoded)} bytes to {board} ({bs.port})"

    async def wait_for(
        self,
        board: str,
        pattern: str,
        timeout_s: float = 30,
    ) -> dict:
        """Wait for a regex pattern to appear in serial output.

        Returns the matching line or a timeout indication.
        """
        bs = self._get_board(board)
        compiled = re.compile(pattern)
        # Check existing buffer first
        with bs.lock:
            for ts, text in reversed(list(bs.buffer)):
                if compiled.search(text):
                    return {"matched": True, "timestamp": ts, "line": text}

        # Set up a waiter
        evt = asyncio.Event()
        holder: list[tuple[str, str]] = []
        loop = asyncio.get_running_loop()
        with bs._waiter_lock:
            bs._waiters.append((compiled, evt, holder, loop))

        try:
            await asyncio.wait_for(evt.wait(), timeout=timeout_s)
        except asyncio.TimeoutError:
            # Remove the waiter
            with bs._waiter_lock:
                bs._waiters = [
                    w for w in bs._waiters if w[1] is not evt
                ]
            return {"matched": False, "timeout": True, "timeout_s": timeout_s}

        ts, line = holder[0]
        return {"matched": True, "timestamp": ts, "line": line}

    def release(self, board: str) -> str:
        return self._get_board(board).release()

    def acquire(self, board: str) -> str:
        return self._get_board(board).acquire()

    def get_raw_lines(self, board: str) -> list[tuple[str, str]]:
        """Return raw (timestamp, line) tuples — used by boot analyzer."""
        bs = self._get_board(board)
        with bs.lock:
            return list(bs.buffer)

    def clear_marker(self, board: str) -> str:
        """Insert a marker line in the buffer (used by bench verifier)."""
        bs = self._get_board(board)
        marker = f"--- bench verify marker {datetime.now(timezone.utc).isoformat()} ---"
        bs._append_line(marker)
        return marker

    # -- internal ---------------------------------------------------------

    def _get_board(self, board: str) -> _BoardSerial:
        if board not in self._board_serials:
            available = ", ".join(self._board_serials.keys()) or "(none)"
            raise ValueError(
                f"Board '{board}' has no serial configuration. "
                f"Available boards with serial: {available}"
            )
        return self._board_serials[board]

    def _load_history(self, bs: _BoardSerial) -> None:
        """Populate ring buffer from tail of disk log file."""
        if not bs.log_file.exists():
            return
        try:
            with open(bs.log_file, "r", encoding="utf-8", errors="replace") as fh:
                tail = collections.deque(fh, maxlen=DISK_TAIL_ON_STARTUP)
            for raw_line in tail:
                raw_line = raw_line.rstrip("\n")
                if "\t" in raw_line:
                    ts, text = raw_line.split("\t", 1)
                else:
                    ts = ""
                    text = raw_line
                bs.buffer.append((ts, text))
        except OSError:
            pass

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
