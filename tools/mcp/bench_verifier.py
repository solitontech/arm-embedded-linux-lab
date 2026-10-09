"""
bench_verifier.py — Scripted bench workflows and verification report generation.

Implements the Agentic FDLC blog's Tier 2 bench verification: reboot a board,
wait for a success or failure pattern in the serial output, run the boot
analyzer, and produce a structured pass/fail result.  Can also generate a
Markdown VERIFICATION_REPORT.md.
"""

from __future__ import annotations

import asyncio
import logging
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import boot_analyzer
from serial_manager import SerialManager
from board_manager import BoardManager

logger = logging.getLogger("lab-mcp.bench")


class BenchVerifier:
    """Tier 2 bench verification: reboot → monitor → analyze → report."""

    def __init__(
        self,
        serial_mgr: SerialManager,
        board_mgr: BoardManager,
        repo_root: Path,
    ):
        self._serial = serial_mgr
        self._board = board_mgr
        self._repo = repo_root
        self._last_result: Optional[dict] = None

    async def verify(
        self,
        board: str,
        success_pattern: str = "login:",
        fail_patterns: Optional[list[str]] = None,
        timeout_s: int = 90,
        reboot_method: Optional[str] = None,
    ) -> dict:
        """Run a full bench verification cycle.

        1. Insert marker in serial buffer
        2. Reboot board
        3. Wait for success or failure pattern
        4. Run boot analyzer on captured output
        5. Return structured result

        Args:
            board: board name
            success_pattern: regex indicating successful boot
            fail_patterns: list of regexes indicating boot failure
            timeout_s: max seconds to wait for pattern match
            reboot_method: override reboot method (default: board config)
        """
        if fail_patterns is None:
            fail_patterns = ["Kernel panic", "Unable to mount root"]

        start_time = time.monotonic()
        start_ts = datetime.now(timezone.utc).isoformat(timespec="milliseconds")

        # 1. Insert marker
        marker = self._serial.clear_marker(board)

        # 2. Reboot
        reboot_result = self._board.reboot(board, method=reboot_method)
        logger.info("Reboot result: %s", reboot_result)

        # 3. Build combined pattern
        combined = f"({success_pattern})|({'|'.join(fail_patterns)})"

        # 4. Wait for match
        wait_result = await self._serial.wait_for(board, combined, timeout_s)

        elapsed = time.monotonic() - start_time

        # 5. Get lines since marker and analyze
        raw_lines = self._serial.get_raw_lines(board)
        # Find marker and take lines after it
        marker_idx = None
        for i, (ts, text) in enumerate(raw_lines):
            if marker in text:
                marker_idx = i
                break
        if marker_idx is not None:
            analysis_lines = raw_lines[marker_idx + 1 :]
        else:
            analysis_lines = raw_lines[-200:]

        analysis = boot_analyzer.analyze(analysis_lines)

        # Determine result
        if not wait_result.get("matched"):
            result_status = "timeout"
        else:
            matched_line = wait_result.get("line", "")
            if re.search(success_pattern, matched_line):
                result_status = "pass"
            else:
                result_status = "fail"

        # Build excerpt (last 50 lines)
        excerpt_lines = [text for _, text in analysis_lines[-50:]]

        result = {
            "result": result_status,
            "board": board,
            "duration_s": round(elapsed, 1),
            "started_at": start_ts,
            "reboot_method": reboot_method or "default",
            "success_pattern": success_pattern,
            "fail_patterns": fail_patterns,
            "matched_line": wait_result.get("line", ""),
            "boot_analysis": analysis.to_dict(),
            "serial_excerpt": "\n".join(excerpt_lines),
        }

        self._last_result = result
        return result

    def generate_report(self, board: str) -> str:
        """Generate a Markdown VERIFICATION_REPORT.md from the last verify run.

        Returns the report content as a string.
        """
        if not self._last_result:
            return "ERROR: No bench verification has been run yet. Call lab_bench_verify first."

        r = self._last_result
        if r["board"] != board:
            return (
                f"ERROR: Last verification was for board '{r['board']}', "
                f"not '{board}'. Run lab_bench_verify for {board} first."
            )

        analysis = r["boot_analysis"]
        status_emoji = {
            "pass": "PASS",
            "fail": "FAIL",
            "timeout": "TIMEOUT",
        }.get(r["result"], r["result"].upper())

        errors_section = ""
        if analysis.get("errors"):
            errors_section = "\n### Errors Detected\n\n"
            for err in analysis["errors"]:
                errors_section += f"**{err['type']}** (line {err['line_number']})\n"
                errors_section += f"- Log: `{err['line']}`\n"
                errors_section += f"- Diagnosis: {err['diagnosis']}\n"
                if err.get("suggested_fixes"):
                    errors_section += "- Suggested fixes:\n"
                    for fix in err["suggested_fixes"]:
                        errors_section += f"  - {fix}\n"
                if err.get("rule_suggestion"):
                    errors_section += f"- Rule suggestion: {err['rule_suggestion']}\n"
                errors_section += "\n"

        warnings_section = ""
        if analysis.get("warnings"):
            warnings_section = "\n### Warnings\n\n"
            for w in analysis["warnings"]:
                warnings_section += f"- {w}\n"

        bootargs_section = ""
        if analysis.get("bootargs_parsed"):
            bootargs_section = "\n### Parsed Bootargs\n\n"
            bootargs_section += "| Key | Value |\n|---|---|\n"
            for k, v in analysis["bootargs_parsed"].items():
                bootargs_section += f"| `{k}` | `{v}` |\n"

        report = f"""# Verification Report — {r['board']}

| Field | Value |
|---|---|
| **Result** | **{status_emoji}** |
| **Board** | {r['board']} |
| **Started** | {r['started_at']} |
| **Duration** | {r['duration_s']}s |
| **Boot Stage** | {analysis.get('boot_stage', 'unknown')} |
| **Progress** | {analysis.get('boot_progress_pct', 0)}% |
| **Reboot Method** | {r['reboot_method']} |
| **Success Pattern** | `{r['success_pattern']}` |
| **Matched Line** | `{r.get('matched_line', '')}` |
{errors_section}{warnings_section}{bootargs_section}
### Serial Log Excerpt (last 50 lines)

```
{r['serial_excerpt']}
```

---
*Generated by ARM Embedded Linux Lab MCP Server (Hardware Tool Bridge)*
"""
        # Write to repo root
        report_path = self._repo / "VERIFICATION_REPORT.md"
        report_path.write_text(report, encoding="utf-8")
        logger.info("Wrote verification report to %s", report_path)

        return report
