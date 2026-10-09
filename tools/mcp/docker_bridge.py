"""
docker_bridge.py — Docker container command execution wrapper.

Provides the Tier 1 (host-side) entry point: runs commands inside the
``arm-lab-dev`` Docker container for cross-compilation, host-side testing,
and build operations.
"""

from __future__ import annotations

import logging
import subprocess
from pathlib import Path

logger = logging.getLogger("lab-mcp.docker")

CONTAINER_NAME = "arm-lab-dev"


class DockerBridge:
    """Execute commands inside the Docker development container."""

    def __init__(self, repo_root: Path):
        self._repo = repo_root

    def exec(self, command: str, timeout: int = 120) -> dict:
        """Run a command inside the Docker container.

        Args:
            command: shell command to execute
            timeout: max seconds to wait (default 120)

        Returns:
            dict with exit_code, stdout, stderr, or error
        """
        # Check if container is running
        if not self._container_running():
            return {
                "error": (
                    f"Docker container '{CONTAINER_NAME}' is not running. "
                    "Start it with: ./lab docker"
                )
            }

        docker_cmd = [
            "docker", "exec", CONTAINER_NAME,
            "bash", "-c", command,
        ]

        try:
            res = subprocess.run(
                docker_cmd,
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
            return {"error": f"Command timed out after {timeout}s"}
        except FileNotFoundError:
            return {"error": "Docker CLI not found. Is Docker installed?"}
        except Exception as exc:
            return {"error": str(exc)}

    def is_running(self) -> bool:
        """Check if the Docker container is currently running."""
        return self._container_running()

    def _container_running(self) -> bool:
        try:
            res = subprocess.run(
                [
                    "docker", "inspect",
                    "--format", "{{.State.Running}}",
                    CONTAINER_NAME,
                ],
                capture_output=True,
                text=True,
                timeout=5,
            )
            return res.stdout.strip() == "true"
        except Exception:
            return False
