"""
docker_bridge.py — Docker container command execution wrapper.

Provides the Tier 1 (host-side) entry point: runs commands inside the
``arm-lab-dev`` Docker container for cross-compilation, host-side testing,
and build operations.
"""

from __future__ import annotations

import logging
import subprocess
import time
from pathlib import Path

logger = logging.getLogger("lab-mcp.docker")

CONTAINER_NAME = "arm-lab-dev"


class DockerBridge:
    """Execute commands inside the Docker development container."""

    def __init__(self, repo_root: Path):
        self._repo = repo_root

    def exec(self, command: str, timeout: int = 120, as_root: bool = False) -> dict:
        """Run a command inside the Docker container.

        Runs as ``labuser`` (host UID) by default so files created in the
        bind-mounted repo are owned by the host user, matching what the
        container entrypoint does for interactive sessions.

        Args:
            command: shell command to execute
            timeout: max seconds to wait (default 120)
            as_root: run as root (only for privileged ops, e.g. exportfs)

        Returns:
            dict with exit_code, stdout, stderr, or error
        """
        # Check if container is running
        if not self._container_running():
            return {
                "error": (
                    f"Docker container '{CONTAINER_NAME}' is not running. "
                    "Start it with the lab_docker_start tool or: ./lab docker start"
                )
            }

        docker_cmd = ["docker", "exec"]
        if not as_root:
            docker_cmd += ["-u", "labuser", "-e", "HOME=/home/labuser"]
        docker_cmd += [CONTAINER_NAME, "bash", "-c", command]

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

    def start(self, timeout: int = 120) -> dict:
        """Start the container detached via ``./lab docker start``.

        Goes through the lab CLI (not raw docker) so HOST_INTERFACE/HOST_IP
        from the board profile are injected. Idempotent if already running.
        """
        if self._container_running():
            return {"status": "already running", "container": CONTAINER_NAME}
        try:
            res = subprocess.run(
                [str(self._repo / "lab"), "docker", "start"],
                capture_output=True, text=True, timeout=timeout,
                cwd=str(self._repo),
            )
        except subprocess.TimeoutExpired:
            return {"error": f"Container start timed out after {timeout}s"}
        except Exception as exc:
            return {"error": str(exc)}

        for _ in range(20):  # entrypoint (tftp/nfs/dnsmasq) may take a moment
            if self._container_running():
                return {"status": "started", "container": CONTAINER_NAME}
            time.sleep(0.5)
        return {
            "error": "Container did not reach running state",
            "exit_code": res.returncode,
            "stdout": res.stdout[-2000:],
            "stderr": res.stderr[-2000:],
        }

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
