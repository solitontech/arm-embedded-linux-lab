#!/usr/bin/env bash
# ==============================================================================
# deploy.sh
# Unified deployment dispatcher for ARM Embedded Linux Lab monorepo.
#
# Supports:
# - SSH / SCP / rsync directly to running target board
# - TFTP deployment (local directory or remote lab host)
# - NFS rootfs deployment (local directory or remote lab host)
# ==============================================================================

set -euo pipefail

# Default variables
BOARD=""
METHOD="ssh"
FILES=""
DEST_DIR="/usr/local/bin"
TARGET_IP=""
TARGET_USER="root"
TARGET_PORT="22"
TARGET_KEY=""
TFTP_BASE="/srv/tftp"
TFTP_SUB=""
NFS_BASE="/srv/nfs"
NFS_ROOTFS=""
LAB_HOST_IP=""
LAB_HOST_USER=""
LAB_HOST_KEY=""
DRY_RUN=false

# ANSI color output
COLOR_BLUE="\033[1;34m"
COLOR_GREEN="\033[1;32m"
COLOR_YELLOW="\033[1;33m"
COLOR_RED="\033[1;31m"
COLOR_RESET="\033[0m"

log_info()    { echo -e "${COLOR_BLUE}[INFO]${COLOR_RESET} $*"; }
log_success() { echo -e "${COLOR_GREEN}[SUCCESS]${COLOR_RESET} $*"; }
log_warn()    { echo -e "${COLOR_YELLOW}[WARN]${COLOR_RESET} $*"; }
log_error()   { echo -e "${COLOR_RED}[ERROR]${COLOR_RESET} $*"; }

# Parse arguments
while [[ $# -gt 0 ]]; do
  case "$1" in
    --board=*) BOARD="${1#*=}" ;;
    --method=*) METHOD="${1#*=}" ;;
    --files=*) FILES="${1#*=}" ;;
    --dest-dir=*) DEST_DIR="${1#*=}" ;;
    --target-ip=*) TARGET_IP="${1#*=}" ;;
    --target-user=*) TARGET_USER="${1#*=}" ;;
    --target-port=*) TARGET_PORT="${1#*=}" ;;
    --target-key=*) TARGET_KEY="${1#*=}" ;;
    --tftp-base=*) TFTP_BASE="${1#*=}" ;;
    --tftp-sub=*) TFTP_SUB="${1#*=}" ;;
    --nfs-base=*) NFS_BASE="${1#*=}" ;;
    --nfs-rootfs=*) NFS_ROOTFS="${1#*=}" ;;
    --lab-host-ip=*) LAB_HOST_IP="${1#*=}" ;;
    --lab-host-user=*) LAB_HOST_USER="${1#*=}" ;;
    --lab-host-key=*) LAB_HOST_KEY="${1#*=}" ;;
    --dry-run) DRY_RUN=true ;;
    -h|--help)
      echo "Usage: $0 [options]"
      echo "  --board=<name>        Target board name (e.g. rpi4, bbb)"
      echo "  --method=<methods>    Deployment method (ssh, tftp, nfs, or combination)"
      echo "  --files=<file1 file2> List of files to deploy"
      echo "  --dest-dir=<path>     Remote target destination directory"
      echo "  --target-ip=<ip>      Target device IP address"
      echo "  --dry-run             Simulate without performing network/file actions"
      exit 0
      ;;
    *)
      log_error "Unknown option: $1"
      exit 1
      ;;
  esac
  shift
done

# Validate inputs
if [ -z "$FILES" ]; then
  log_error "No files specified for deployment (--files=<files>)"
  exit 1
fi

for f in $FILES; do
  if [ ! -e "$f" ]; then
    log_error "Artifact not found: $f (did you build the project first?)"
    exit 1
  fi
done

# ------------------------------------------------------------------------------
# SSH Deployment
# ------------------------------------------------------------------------------
deploy_ssh() {
  log_info "Deploying via SSH/SCP to target..."
  if [ -z "$TARGET_IP" ]; then
    log_error "TARGET_IP is not set. Please configure tools/deploy/boards/${BOARD}.env"
    return 1
  fi

  local SSH_OPTS=(-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o ConnectTimeout=5)
  if [ -n "$TARGET_PORT" ]; then SSH_OPTS+=(-p "$TARGET_PORT"); fi
  if [ -n "$TARGET_KEY" ] && [ -f "$TARGET_KEY" ]; then SSH_OPTS+=(-i "$TARGET_KEY"); fi

  local SCP_PORT_OPT=""
  if [ -n "$TARGET_PORT" ]; then SCP_PORT_OPT="-P $TARGET_PORT"; fi
  local SCP_KEY_OPT=""
  if [ -n "$TARGET_KEY" ] && [ -f "$TARGET_KEY" ]; then SCP_KEY_OPT="-i $TARGET_KEY"; fi

  if [ "$DRY_RUN" = true ]; then
    log_info "[DRY-RUN] Would create remote dir: ssh ${TARGET_USER}@${TARGET_IP} 'mkdir -p ${DEST_DIR}'"
    log_info "[DRY-RUN] Would copy files: scp $FILES ${TARGET_USER}@${TARGET_IP}:${DEST_DIR}/"
    log_info "[DRY-RUN] Would set executable: ssh ${TARGET_USER}@${TARGET_IP} 'chmod +x ${DEST_DIR}/*'"
    return 0
  fi

  # Check host reachability
  log_info "Connecting to ${TARGET_USER}@${TARGET_IP}..."
  if ! ssh "${SSH_OPTS[@]}" "${TARGET_USER}@${TARGET_IP}" "mkdir -p '${DEST_DIR}'" 2>/dev/null; then
    log_error "Failed to connect to ${TARGET_USER}@${TARGET_IP} via SSH."
    log_error "Ensure board is powered on, connected to the lab network, and SSH key is valid."
    return 1
  fi

  # Transfer files
  # shellcheck disable=SC2086
  scp -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null $SCP_PORT_OPT $SCP_KEY_OPT $FILES "${TARGET_USER}@${TARGET_IP}:${DEST_DIR}/"

  # Ensure executable permission
  for f in $FILES; do
    local bname
    bname=$(basename "$f")
    ssh "${SSH_OPTS[@]}" "${TARGET_USER}@${TARGET_IP}" "chmod +x '${DEST_DIR}/${bname}' 2>/dev/null || true"
  done

  log_success "Deployed $(echo "$FILES" | tr '\n' ' ') to ${TARGET_USER}@${TARGET_IP}:${DEST_DIR}/"
}

# ------------------------------------------------------------------------------
# TFTP Deployment
# ------------------------------------------------------------------------------
deploy_tftp() {
  local sub_dir="${TFTP_SUB:-$BOARD}"
  local full_tftp_dir="${TFTP_BASE}/${sub_dir}"
  log_info "Deploying via TFTP to: ${full_tftp_dir}..."

  if [ "$DRY_RUN" = true ]; then
    log_info "[DRY-RUN] Would deploy files to TFTP directory: ${full_tftp_dir}"
    return 0
  fi

  # Check if TFTP directory is locally accessible or remote lab host
  if [ -d "$TFTP_BASE" ] || [ -w "$(dirname "$TFTP_BASE" 2>/dev/null || true)" ]; then
    mkdir -p "$full_tftp_dir"
    for f in $FILES; do
      cp -v "$f" "$full_tftp_dir/"
    done
    log_success "Copied files to local TFTP directory: ${full_tftp_dir}"
  elif [ -n "$LAB_HOST_IP" ]; then
    log_info "Deploying to remote lab host TFTP (${LAB_HOST_USER:-root}@${LAB_HOST_IP}:${full_tftp_dir})..."
    local SSH_KEY_OPT=""
    if [ -n "$LAB_HOST_KEY" ] && [ -f "$LAB_HOST_KEY" ]; then SSH_KEY_OPT="-i $LAB_HOST_KEY"; fi
    
    ssh -o StrictHostKeyChecking=no $SSH_KEY_OPT "${LAB_HOST_USER:-root}@${LAB_HOST_IP}" "mkdir -p '${full_tftp_dir}'"
    # shellcheck disable=SC2086
    scp -o StrictHostKeyChecking=no $SSH_KEY_OPT $FILES "${LAB_HOST_USER:-root}@${LAB_HOST_IP}:${full_tftp_dir}/"
    log_success "Copied files to remote lab host TFTP server: ${full_tftp_dir}"
  else
    log_warn "TFTP directory '${full_tftp_dir}' is not writable locally and LAB_HOST_IP is not set."
    log_warn "Creating local staging folder: ./build/${BOARD}/tftp_staging/"
    mkdir -p "./build/${BOARD}/tftp_staging/"
    for f in $FILES; do
      cp -v "$f" "./build/${BOARD}/tftp_staging/"
    done
  fi
}

# ------------------------------------------------------------------------------
# NFS Rootfs Deployment
# ------------------------------------------------------------------------------
deploy_nfs() {
  local rootfs="${NFS_ROOTFS:-${BOARD}/rootfs}"
  local full_nfs_dir="${NFS_BASE}/${rootfs}/${DEST_DIR#/}"
  log_info "Deploying via NFS rootfs to: ${full_nfs_dir}..."

  if [ "$DRY_RUN" = true ]; then
    log_info "[DRY-RUN] Would deploy files to NFS path: ${full_nfs_dir}"
    return 0
  fi

  if [ -d "$NFS_BASE" ] || [ -w "$(dirname "$NFS_BASE" 2>/dev/null || true)" ]; then
    mkdir -p "$full_nfs_dir"
    for f in $FILES; do
      install -m 755 "$f" "$full_nfs_dir/"
    done
    log_success "Installed files to local NFS rootfs: ${full_nfs_dir}"
  elif [ -n "$LAB_HOST_IP" ]; then
    log_info "Deploying to remote lab host NFS rootfs (${LAB_HOST_USER:-root}@${LAB_HOST_IP}:${full_nfs_dir})..."
    local SSH_KEY_OPT=""
    if [ -n "$LAB_HOST_KEY" ] && [ -f "$LAB_HOST_KEY" ]; then SSH_KEY_OPT="-i $LAB_HOST_KEY"; fi

    ssh -o StrictHostKeyChecking=no $SSH_KEY_OPT "${LAB_HOST_USER:-root}@${LAB_HOST_IP}" "mkdir -p '${full_nfs_dir}'"
    # shellcheck disable=SC2086
    scp -o StrictHostKeyChecking=no $SSH_KEY_OPT $FILES "${LAB_HOST_USER:-root}@${LAB_HOST_IP}:${full_nfs_dir}/"
    for f in $FILES; do
      local bname
      bname=$(basename "$f")
      ssh -o StrictHostKeyChecking=no $SSH_KEY_OPT "${LAB_HOST_USER:-root}@${LAB_HOST_IP}" "chmod 755 '${full_nfs_dir}/${bname}'"
    done
    log_success "Installed files to remote NFS rootfs: ${full_nfs_dir}"
  else
    log_warn "NFS base directory '${NFS_BASE}' not found locally and LAB_HOST_IP is not set."
  fi
}

# ------------------------------------------------------------------------------
# Dispatch methods
# ------------------------------------------------------------------------------
for m in $METHOD; do
  case "$m" in
    ssh|scp)  deploy_ssh ;;
    tftp)     deploy_tftp ;;
    nfs)      deploy_nfs ;;
    custom)   log_info "Custom deployment handled by project hooks." ;;
    *)
      log_error "Unknown deployment method: $m (supported: ssh, tftp, nfs, custom)"
      exit 1
      ;;
  esac
done
