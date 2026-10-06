#!/usr/bin/env bash
# ==============================================================================
# tools/docker/run.sh — ARM Embedded Linux Lab Docker Helper
# Usage:
#   ./tools/docker/run.sh build          Build the Docker image
#   ./tools/docker/run.sh run            Start an interactive container
#   ./tools/docker/run.sh stop           Stop and remove the running container
#   ./tools/docker/run.sh exec <cmd>     Run a command inside a running container
#   ./tools/docker/run.sh push           Push image to registry (set REGISTRY env var)
# ==============================================================================
set -euo pipefail

IMAGE_NAME="arm-embedded-linux-lab"
IMAGE_TAG="${IMAGE_TAG:-latest}"
CONTAINER_NAME="arm-lab-dev"
REGISTRY="${REGISTRY:-}"   # e.g. ghcr.io/your-org

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

# ── Colour helpers ──────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[0;33m'; CYAN='\033[0;36m'; BOLD='\033[1m'; RESET='\033[0m'
info()  { echo -e "${BOLD}${CYAN}❯ [INFO]${RESET} $*"; }
ok()    { echo -e "${BOLD}${GREEN}✔ [OK]${RESET} $*"; }
warn()  { echo -e "${BOLD}${YELLOW}⚠ [WARN]${RESET} $*"; }
err()   { echo -e "${BOLD}${RED}✖ [ERROR]${RESET} $*" >&2; exit 1; }

# ── OS detection & Docker prerequisite check ────────────────────────────────
check_docker() {
    if ! command -v docker &>/dev/null; then
        echo ""
        err "Docker is not installed or not in PATH.
Run the automated installer for your OS:
  ./tools/docker/run.sh install-docker

Or install manually:
  macOS   → https://docs.docker.com/desktop/mac/install/ (or: brew install --cask docker)
  Linux   → https://docs.docker.com/engine/install/ (or: curl -fsSL https://get.docker.com | sh)
  Windows → https://docs.docker.com/desktop/windows/install/ (enable WSL2 backend)"
    fi

    if ! docker info &>/dev/null; then
        local err_msg
        err_msg="$(docker info 2>&1 || true)"
        if echo "$err_msg" | grep -qi "permission denied"; then
            err "Permission denied while connecting to Docker daemon socket.
To fix this permission issue on Linux, run:
  sudo usermod -aG docker \$USER && newgrp docker

Or run with sudo:
  sudo ./tools/docker/run.sh <command>"
        fi
    fi
}

cmd_install_docker() {
    if command -v docker &>/dev/null; then
        ok "Docker is already installed ($(docker --version))."
        if docker info &>/dev/null; then
            ok "Docker daemon is running and responsive."
        else
            warn "Docker CLI is installed, but daemon is not running. Please start Docker Desktop or the dockerd service."
        fi
        return 0
    fi

    local os
    os="$(uname -s)"
    info "Detected Operating System: ${os}"

    case "$os" in
        Darwin)
            info "Starting Docker Desktop installation for macOS..."
            if command -v brew &>/dev/null; then
                info "Found Homebrew. Installing Docker Desktop via Homebrew Cask..."
                brew install --cask docker
                ok "Docker Desktop installed to /Applications/Docker.app"
                info "Starting Docker Desktop..."
                open -a Docker || true
                ok "Docker Desktop launched. Please complete initial setup in the application window."
            else
                info "Homebrew not found. Please install Homebrew (https://brew.sh) or download Docker Desktop directly:"
                local arch
                arch="$(uname -m)"
                if [[ "$arch" == "arm64" ]]; then
                    echo "  Apple Silicon (M1/M2/M3/M4): https://desktop.docker.com/mac/main/arm64/Docker.dmg"
                else
                    echo "  Intel Mac: https://desktop.docker.com/mac/main/amd64/Docker.dmg"
                fi
            fi
            ;;

        Linux)
            info "Installing Docker on Linux using the official convenience script..."
            if command -v curl &>/dev/null; then
                curl -fsSL https://get.docker.com | sh
            elif command -v wget &>/dev/null; then
                wget -qO- https://get.docker.com | sh
            else
                err "Neither curl nor wget found. Please install curl/wget or Docker manually."
            fi

            info "Adding current user ($USER) to the docker group..."
            sudo usermod -aG docker "$USER" || true
            ok "Docker installed. Note: You may need to log out and back in for group membership to take effect."
            ;;

        CYGWIN*|MINGW*|MSYS*)
            info "Detected Windows environment."
            if command -v winget.exe &>/dev/null; then
                info "Installing Docker Desktop via winget..."
                winget.exe install Docker.DockerDesktop
                ok "Docker Desktop installed. Please start Docker Desktop and ensure WSL2 integration is enabled."
            else
                echo "Please download and install Docker Desktop for Windows:
  https://docs.docker.com/desktop/windows/install/"
            fi
            ;;

        *)
            err "Unsupported OS '${os}'. Please install Docker manually from https://docs.docker.com/get-docker/"
            ;;
    esac
}

# ── Subcommands ─────────────────────────────────────────────────────────────
cmd_build() {
    check_docker
    local full_name="${IMAGE_NAME}:${IMAGE_TAG}"
    [[ -n "$REGISTRY" ]] && full_name="${REGISTRY}/${full_name}"

    info "Building Docker image: ${full_name}"
    local target_uid="${SUDO_UID:-$(id -u)}"
    local target_gid="${SUDO_GID:-$(id -g)}"
    if [[ "$target_uid" -eq 0 ]]; then
        target_uid=1000
        target_gid=1000
    fi

    docker build \
        --build-arg UID="${target_uid}" \
        --build-arg GID="${target_gid}" \
        -t "${full_name}" \
        -f "${REPO_ROOT}/tools/docker/Dockerfile" \
        "${REPO_ROOT}"
    ok "Image built: ${full_name}"
}

cmd_run() {
    check_docker
    local full_name="${IMAGE_NAME}:${IMAGE_TAG}"
    [[ -n "$REGISTRY" ]] && full_name="${REGISTRY}/${full_name}"

    # If already running, seamlessly attach instead of failing with a name conflict
    if docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
        info "Container '${CONTAINER_NAME}' is already running. Attaching to existing session..."
        docker exec -it "${CONTAINER_NAME}" /bin/bash
        return 0
    fi

    # Clean up any stopped or stale container with the same name
    if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
        docker rm -f "${CONTAINER_NAME}" &>/dev/null || true
    fi

    # ── Serial device passthrough ──────────────────────────────────────────
    # Linux host: pass /dev/ttyUSB* and /dev/ttyACM* directly via --device.
    #
    # macOS host: Docker Desktop runs in a Linux VM and cannot forward
    # /dev/cu.* paths. Instead we start a socat TCP listener on the host for
    # each serial device, then the container entrypoint connects back via
    # TCP and creates a PTY at /dev/ttyVUSB<N> so picocom works normally.
    local device_flags=()
    local detected_devices=()
    local serial_proxy_ports=""   # "port:origdev,..." passed as env var
    local socat_pids=()
    local SOCAT_PID_FILE="/tmp/.arm-lab-socat-pids"

    # Linux-style devices (direct passthrough)
    for dev in /dev/ttyUSB* /dev/ttyACM*; do
        if [[ -c "$dev" ]]; then
            device_flags+=(--device "${dev}:${dev}")
            detected_devices+=("$dev")
        fi
    done

    # macOS-style devices — bridge each one via socat TCP
    local macos_devices=()
    for dev in /dev/cu.usbserial* /dev/cu.usbmodem*; do
        [[ -c "$dev" ]] && macos_devices+=("$dev")
    done

    if [[ ${#detected_devices[@]} -gt 0 ]]; then
        ok "Passing serial devices into container: ${detected_devices[*]}"

    elif [[ ${#macos_devices[@]} -gt 0 ]]; then
        # Ensure socat is available on the host
        if ! command -v socat &>/dev/null; then
            warn "socat not found — installing via Homebrew for serial bridging..."
            HOMEBREW_NO_INTERACTIVE=1 brew install socat || err "Could not install socat. Run: brew install socat"
        fi

        # Ensure any leftover socat instances from previous sessions are killed
        if [[ -f "${SOCAT_PID_FILE}" ]]; then
            while IFS= read -r pid; do
                kill "$pid" 2>/dev/null || true
            done < "${SOCAT_PID_FILE}"
            rm -f "${SOCAT_PID_FILE}"
        fi

        local port=54320
        local entries=()
        for dev in "${macos_devices[@]}"; do
            info "Bridging ${dev} → TCP 0.0.0.0:${port} → /dev/ttyVUSB${#entries[@]} in container"
            socat TCP-LISTEN:${port},reuseaddr,fork \
                  OPEN:"${dev}",ispeed=115200,ospeed=115200,raw,echo=0 &>/dev/null &
            socat_pids+=($!)
            entries+=("${port}:${dev}")
            port=$(( port + 1 ))
        done

        # Save socat PIDs so cmd_stop can clean them up
        printf '%s\n' "${socat_pids[@]}" > "${SOCAT_PID_FILE}"

        # Build comma-separated env var for the container entrypoint
        serial_proxy_ports="$(IFS=','; echo "${entries[*]}")"
        ok "Serial bridge(s) ready. Inside container: picocom -b 115200 /dev/ttyVUSB0"

    else
        warn "No USB-serial adapter detected on host (/dev/ttyUSB*, /dev/ttyACM*, /dev/cu.*)."
        warn "Plug in your USB-serial adapter and re-run to get serial access."
    fi

    info "Starting container '${CONTAINER_NAME}' with repo mounted at /workspace..."
    docker run \
        --rm \
        -it \
        --network host \
        --name "${CONTAINER_NAME}" \
        -v "${REPO_ROOT}:/workspace" \
        -w /workspace \
        ${serial_proxy_ports:+-e "SERIAL_PROXY_PORTS=${serial_proxy_ports}"} \
        ${device_flags[@]+"${device_flags[@]}"} \
        "${full_name}"

    # Container exited — clean up any host socat bridges
    if [[ -f "${SOCAT_PID_FILE}" ]]; then
        while IFS= read -r pid; do
            kill "$pid" 2>/dev/null || true
        done < "${SOCAT_PID_FILE}"
        rm -f "${SOCAT_PID_FILE}"
    fi
}

cmd_exec() {
    check_docker
    [[ $# -lt 1 ]] && err "Usage: $0 exec <command> [args...]"
    info "Executing in container '${CONTAINER_NAME}': $*"
    docker exec -it "${CONTAINER_NAME}" "$@"
}

cmd_attach() {
    check_docker
    if docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
        info "Attaching new shell session to running container '${CONTAINER_NAME}'..."
        docker exec -it "${CONTAINER_NAME}" /bin/bash
    else
        warn "Container '${CONTAINER_NAME}' is not currently running. Starting a new container..."
        cmd_run
    fi
}

cmd_stop() {
    check_docker
    info "Stopping container '${CONTAINER_NAME}' (if running)..."
    docker stop "${CONTAINER_NAME}" &>/dev/null || true
    local rm_out
    rm_out=$(docker rm -f "${CONTAINER_NAME}" 2>&1) && \
        ok "Container '${CONTAINER_NAME}' stopped and removed." || \
        { echo "$rm_out" | grep -qi "no such container" && \
            ok "Container '${CONTAINER_NAME}' is not running." || \
            err "Failed to remove container: ${rm_out}"; }

    # Kill any host socat serial bridge processes
    local SOCAT_PID_FILE="/tmp/.arm-lab-socat-pids"
    if [[ -f "${SOCAT_PID_FILE}" ]]; then
        while IFS= read -r pid; do
            kill "$pid" 2>/dev/null || true
        done < "${SOCAT_PID_FILE}"
        rm -f "${SOCAT_PID_FILE}"
        ok "Host serial bridge(s) stopped."
    fi
}

cmd_push() {
    [[ -z "$REGISTRY" ]] && err "Set REGISTRY env var before pushing (e.g. REGISTRY=ghcr.io/your-org)"
    cmd_build  # ensure latest build
    local full_name="${REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}"
    info "Pushing ${full_name}..."
    docker push "${full_name}"
    ok "Pushed: ${full_name}"
}

# ── Dispatch ─────────────────────────────────────────────────────────────────
COMMAND="${1:-help}"
shift || true

case "$COMMAND" in
    install-docker|install) cmd_install_docker ;;
    build)  cmd_build ;;
    run)    cmd_run ;;
    stop)   cmd_stop ;;
    attach) cmd_attach ;;
    exec)   cmd_exec "$@" ;;
    push)   cmd_push ;;
    help|--help|-h)
        echo ""
        echo -e "${BOLD}ARM Embedded Linux Lab — Docker Helper${RESET}"
        echo ""
        echo "  install-docker  Install Docker on the host PC (macOS, Linux, Windows)"
        echo "  build           Build the development Docker image"
        echo "  run             Start an interactive container (repo mounted at /workspace)"
        echo "  stop            Stop and remove the running container"
        echo "  attach          Reconnect/open a shell into the already running container"
        echo "  exec <cmd>      Run a command inside the running container"
        echo "  push            Push the image to \$REGISTRY (set REGISTRY env var)"
        echo ""
        echo "Environment variables:"
        echo "  IMAGE_TAG       Tag for the Docker image (default: latest)"
        echo "  REGISTRY        Remote registry prefix (e.g. ghcr.io/your-org)"
        ;;
    *)  err "Unknown command: ${COMMAND}. Run '$0 --help' for usage." ;;
esac
