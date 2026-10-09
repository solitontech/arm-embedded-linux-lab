#!/usr/bin/env bash
# ==============================================================================
# setup_venv.sh — Create and populate the MCP server virtual environment
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${SCRIPT_DIR}/venv"

echo "==> Creating virtual environment at ${VENV_DIR} ..."
python3 -m venv "${VENV_DIR}"

echo "==> Installing dependencies ..."
"${VENV_DIR}/bin/pip" install --upgrade pip
"${VENV_DIR}/bin/pip" install -r "${SCRIPT_DIR}/requirements.txt"

echo "==> Installed packages:"
"${VENV_DIR}/bin/pip" list

echo ""
echo "✔ MCP server venv ready."
echo "  Start the server:    ${VENV_DIR}/bin/python ${SCRIPT_DIR}/server.py"
echo "  Or use the lab CLI:  ./lab mcp start"
