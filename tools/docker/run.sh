#!/usr/bin/env bash
# ==============================================================================
# tools/docker/run.sh — ARM Embedded Linux Lab Docker Helper
# Usage:
#   ./tools/docker/run.sh build          Build the Docker image
#   ./tools/docker/run.sh run            Start an interactive container
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
    docker build \
        --build-arg UID="$(id -u)" \
        --build-arg GID="$(id -g)" \
        -t "${full_name}" \
        -f "${REPO_ROOT}/tools/docker/Dockerfile" \
        "${REPO_ROOT}"
    ok "Image built: ${full_name}"
}

cmd_run() {
    check_docker
    local full_name="${IMAGE_NAME}:${IMAGE_TAG}"
    [[ -n "$REGISTRY" ]] && full_name="${REGISTRY}/${full_name}"

    info "Starting container '${CONTAINER_NAME}' with repo mounted at /workspace..."
    docker run \
        --rm \
        -it \
        --name "${CONTAINER_NAME}" \
        --user "$(id -u):$(id -g)" \
        -v "${REPO_ROOT}:/workspace" \
        -w /workspace \
        "${full_name}"
}

cmd_exec() {
    check_docker
    [[ $# -lt 1 ]] && err "Usage: $0 exec <command> [args...]"
    info "Executing in container '${CONTAINER_NAME}': $*"
    docker exec -it "${CONTAINER_NAME}" "$@"
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
    exec)   cmd_exec "$@" ;;
    push)   cmd_push ;;
    help|--help|-h)
        echo ""
        echo -e "${BOLD}ARM Embedded Linux Lab — Docker Helper${RESET}"
        echo ""
        echo "  install-docker  Install Docker on the host PC (macOS, Linux, Windows)"
        echo "  build           Build the development Docker image"
        echo "  run             Start an interactive container (repo mounted at /workspace)"
        echo "  exec <cmd>      Run a command inside the running container"
        echo "  push            Push the image to \$REGISTRY (set REGISTRY env var)"
        echo ""
        echo "Environment variables:"
        echo "  IMAGE_TAG       Tag for the Docker image (default: latest)"
        echo "  REGISTRY        Remote registry prefix (e.g. ghcr.io/your-org)"
        ;;
    *)  err "Unknown command: ${COMMAND}. Run '$0 --help' for usage." ;;
esac
