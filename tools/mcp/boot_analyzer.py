"""
boot_analyzer.py — Boot log pattern engine for diagnosing embedded Linux boot issues.

Scans serial log lines and returns a structured analysis: detected boot stage,
progress estimate, classified errors with diagnosis and suggested fixes, and
a parsed representation of kernel bootargs.  Each error includes a
``rule_suggestion`` field that the agent can propose adding to AGENT_RULES.md
(the Agentic FDLC "institutional knowledge capture" pattern).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field, asdict
from typing import Optional


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------
@dataclass
class BootError:
    type: str
    line_number: int
    line: str
    diagnosis: str
    suggested_fixes: list[str] = field(default_factory=list)
    rule_suggestion: str = ""


@dataclass
class BootAnalysis:
    boot_stage: str = "unknown"
    boot_progress_pct: int = 0
    errors: list[BootError] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    last_line: str = ""
    bootargs_parsed: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)


# ---------------------------------------------------------------------------
# Stage progression (order matters — later entries override earlier)
# ---------------------------------------------------------------------------
_STAGE_PATTERNS: list[tuple[str, str, int]] = [
    # (regex, stage_name, progress_pct)
    (r"U-Boot\s+\d{4}\.\d{2}", "u-boot", 10),
    (r"Hit any key to stop autoboot", "u-boot", 15),
    (r"(U-Boot>|=>)\s*$", "u-boot-prompt", 20),
    (r"==> Fetching kernel", "u-boot-tftp", 25),
    (r"==> Fetching Device Tree", "u-boot-tftp", 30),
    (r"==> Booting Linux kernel", "u-boot-boot", 35),
    (r"Starting kernel \.\.\.", "u-boot-handoff", 40),
    (r"Booting Linux on physical CPU", "kernel", 45),
    (r"Kernel command line:", "kernel", 50),
    (r"Calibrating delay loop", "kernel", 55),
    (r"NET: Registered", "kernel", 60),
    (r"IP-Config:", "kernel-ip", 65),
    (r"rootpath=", "kernel-ip", 67),
    (r"NFS: nfs mount opts", "kernel-nfs", 70),
    (r"VFS: Mounted root", "kernel-rootfs", 75),
    (r"Run /sbin/init", "init", 80),
    (r"mount -t devtmpfs", "init-early", 85),
    (r"Welcome to.*Lab|rcS|init\.d", "init-scripts", 90),
    (r"(Please press Enter|login:)", "userspace", 100),
]

# ---------------------------------------------------------------------------
# Error patterns
# ---------------------------------------------------------------------------
_ERROR_PATTERNS: list[tuple[str, str, str, list[str], str]] = [
    # (regex, error_type, diagnosis, suggested_fixes, rule_suggestion)
    (
        r"Kernel panic",
        "kernel_panic",
        "Kernel panic — the kernel encountered a fatal error and halted",
        [
            "Check serial log for the panic message and call trace",
            "Verify kernel config matches hardware (DTB, rootfs type)",
            "Ensure /dev/console exists in NFS rootfs",
        ],
        "Verify /dev/console and /dev/null exist in rootfs before deploying",
    ),
    (
        r"VFS: Unable to mount root fs",
        "rootfs_mount_failure",
        "Kernel cannot mount the root filesystem",
        [
            "Check boot.cmd: root= and nfsroot= parameters",
            "Verify NFS server is running: run lab_doctor",
            "Ensure kernel has CONFIG_NFS_FS=y, CONFIG_ROOT_NFS=y built-in (not modules)",
        ],
        "Always verify kernel NFS config is built-in (=y, not =m) before TFTP boot",
    ),
    (
        r"NFS:.*server .* not responding|nfs.*timed out",
        "nfs_mount_timeout",
        "Kernel cannot reach NFS server — mount timed out",
        [
            "Verify Docker container has NFS server running (lab_doctor section 6)",
            "Check NFS export path matches nfsroot= in boot.cmd",
            "Verify network: board IP can reach host IP (ping from U-Boot)",
        ],
        "Always verify NFS export path matches boot.cmd nfsroot= before deploying",
    ),
    (
        r"FDT.*overlaps",
        "dtb_overlap",
        "Device Tree Blob load address overlaps with kernel image in memory",
        [
            "Increase DTB load address in boot.cmd (e.g. 0x06000000)",
            "Check that kernel Image size hasn't grown past the DTB region",
        ],
        "Ensure DTB load address is well above kernel Image end (check with tftp size)",
    ),
    (
        r"TFTP error|T T T",
        "tftp_timeout",
        "U-Boot TFTP transfer failed or timed out",
        [
            "Verify TFTP server is running: lab_doctor section 5",
            "Check serverip matches host IP in boot.cmd",
            "Ensure kernel Image and DTB exist in tftp/ directory",
        ],
        "Verify TFTP server is running and files exist before rebooting the board",
    ),
    (
        r"Synchronous Abort|Unhandled fault|Oops",
        "cpu_exception",
        "CPU exception — likely a bad memory access or corrupted image",
        [
            "Re-download kernel Image and DTB via TFTP",
            "Check for DRAM configuration issues in U-Boot",
            "Verify the Image is built for the correct architecture (arm64)",
        ],
        "After kernel rebuild, always verify architecture matches target board",
    ),
    (
        r"can't run '/etc/init\.d/rcS'|can't execute",
        "init_exec_fail",
        "Init cannot execute rcS or the init binary",
        [
            "Verify /etc/init.d/rcS has execute permission (chmod +x)",
            "Check that busybox binary is present in /bin/ and /sbin/",
            "Ensure rootfs was built for the correct architecture",
        ],
        "Verify rcS has +x permission and busybox is present before NFS boot",
    ),
]

# ---------------------------------------------------------------------------
# Warning patterns
# ---------------------------------------------------------------------------
_WARNING_PATTERNS: list[tuple[str, str]] = [
    (r"rootpath=\s*$", "rootpath= is empty (expected for static IP, not an error)"),
    (
        r"bootconsole.*disabled",
        "Boot console disabled — output may pause during console switch. "
        "If the system appears stuck here, check earlycon= or console= in bootargs.",
    ),
    (
        r"random: crng init done",
        "CRNG initialized — may cause boot delay on systems with low entropy",
    ),
]


# ---------------------------------------------------------------------------
# Bootargs parser
# ---------------------------------------------------------------------------
def _parse_bootargs(line: str) -> dict[str, str]:
    """Extract key=value pairs from a 'Kernel command line:' log line."""
    # Strip the prefix
    match = re.search(r"Kernel command line:\s*(.*)", line)
    if not match:
        return {}
    cmdline = match.group(1)
    result: dict[str, str] = {}
    for token in cmdline.split():
        if "=" in token:
            k, _, v = token.partition("=")
            result[k] = v
        else:
            result[token] = ""
    return result


# ---------------------------------------------------------------------------
# Main analysis function
# ---------------------------------------------------------------------------
def analyze(lines: list[tuple[str, str]]) -> BootAnalysis:
    """Analyze serial log lines and return structured boot analysis.

    Args:
        lines: list of (timestamp, line_text) tuples from SerialManager

    Returns:
        BootAnalysis with stage, progress, errors, warnings, bootargs
    """
    analysis = BootAnalysis()
    if not lines:
        return analysis

    analysis.last_line = lines[-1][1] if lines else ""

    for idx, (ts, text) in enumerate(lines):
        # Stage detection (latest match wins)
        for pat, stage, pct in _STAGE_PATTERNS:
            if re.search(pat, text):
                analysis.boot_stage = stage
                analysis.boot_progress_pct = pct

        # Error detection
        for pat, etype, diagnosis, fixes, rule_sug in _ERROR_PATTERNS:
            if re.search(pat, text):
                analysis.errors.append(
                    BootError(
                        type=etype,
                        line_number=idx,
                        line=text,
                        diagnosis=diagnosis,
                        suggested_fixes=fixes,
                        rule_suggestion=rule_sug,
                    )
                )

        # Warning detection
        for pat, msg in _WARNING_PATTERNS:
            if re.search(pat, text):
                if msg not in analysis.warnings:
                    analysis.warnings.append(msg)

        # Bootargs parsing
        if "Kernel command line:" in text:
            analysis.bootargs_parsed = _parse_bootargs(text)

    return analysis
