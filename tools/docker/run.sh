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
RED='\033[0;31m'; GREEN='\033[0;32m'; CYAN='\033[0;36m'; BOLD='\033[1m'; RESET='\033[0m'
info()  { echo -e "${BOLD}${CYAN}❯ [INFO]${RESET} $*"; }
ok()    { echo -e "${BOLD}${GREEN}✔ [OK]${RESET} $*"; }
err()   { echo -e "${BOLD}${RED}✖ [ERROR]${RESET} $*" >&2; exit 1; }

# ── OS detection & Docker prerequisite check ────────────────────────────────
check_docker() {
    if ! command -v docker &>/dev/null; then
        local os
        os="$(uname -s)"
        echo ""
        err "Docker not found. Install it first:
  macOS   → https://docs.docker.com/desktop/mac/install/
  Linux   → https://docs.docker.com/engine/install/
  Windows → https://docs.docker.com/desktop/windows/install/ (enable WSL2 backend)"
    fi
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
    build)  cmd_build ;;
    run)    cmd_run ;;
    exec)   cmd_exec "$@" ;;
    push)   cmd_push ;;
    help|--help|-h)
        echo ""
        echo -e "${BOLD}ARM Embedded Linux Lab — Docker Helper${RESET}"
        echo ""
        echo "  build        Build the development Docker image"
        echo "  run          Start an interactive container (repo mounted at /workspace)"
        echo "  exec <cmd>   Run a command inside the running container"
        echo "  push         Push the image to \$REGISTRY (set REGISTRY env var)"
        echo ""
        echo "Environment variables:"
        echo "  IMAGE_TAG    Tag for the Docker image (default: latest)"
        echo "  REGISTRY     Remote registry prefix (e.g. ghcr.io/your-org)"
        ;;
    *)  err "Unknown command: ${COMMAND}. Run '$0 --help' for usage." ;;
esac
