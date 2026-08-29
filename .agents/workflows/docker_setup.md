---
description: How to set up the Docker development environment for a new PC (any OS)
---

# Docker Setup Workflow

## When to Use This Workflow
Use this workflow when:
- Setting up the ARM Embedded Linux Lab on a **new PC** for the first time.
- Cross-compilers are not installed natively and you want a one-command environment.
- Onboarding a new team member.
- Running builds in a CI pipeline.

## Prerequisites
- Git and Docker installed (see links in `.agents/skills/docker-setup/SKILL.md`).
- Repository cloned locally.

## Steps

### 1. Clone the repository (if not already done)
```bash
git clone <repo-url>
cd arm-embedded-linux-lab
```

### 2. Install Docker (if not already installed)
```bash
./tools/docker/run.sh install-docker
```
Auto-detects host OS and runs the appropriate installer (macOS Homebrew, Linux script, Windows winget).

### 3. Build the Docker image
```bash
./tools/docker/run.sh build
```
This compiles an Ubuntu 22.04 image with all required toolchains. Takes ~2–5 minutes on first run; cached on subsequent runs.

### 4. Verify the environment
```bash
./tools/docker/run.sh run
# Inside the container:
./lab doctor
```
All toolchains (`aarch64-linux-gnu-gcc`, `gdb-multiarch`, `picocom`, etc.) should show ✔.

### 5. Build a project inside the container
```bash
# Still inside the container:
./lab build myproject --board rpi4
```

### 6. Exit and re-enter as needed
```bash
exit   # leave the container (--rm removes it automatically)
./tools/docker/run.sh run   # re-enter anytime; your source edits are preserved on the host
```

### 7. (Optional) Push to registry for CI/team use
```bash
REGISTRY=ghcr.io/your-org ./tools/docker/run.sh push
```

## Skill Reference
See `.agents/skills/docker-setup/SKILL.md` for the full command reference and troubleshooting notes.

## Files Touched
- `[NONE]` – no source files are modified by this workflow; it is purely environment setup.
