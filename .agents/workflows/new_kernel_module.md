---
description: how to add and run a new out-of-tree kernel module for a board
---

# New Kernel Module

## When to Use This Workflow
Use when creating a new out-of-tree kernel module under `projects/`.

## Prerequisites
- See [kernel-module-dev skill](../skills/kernel-module-dev/SKILL.md): Docker up, the board netbooting from `nfs/<board>-rootfs`, and a `KDIR` that matches the booted kernel (`make -C shared/kernel kdir-from-image KERNEL_RELEASE_SUFFIX=<from uname -r>`).

## Steps

1. **Scaffold**
   ```bash
   cp -r shared/templates/kmod_project projects/<name>
   ```
   Set `MODULE_NAME` in the Makefile and rename the `.c` file to match.

2. **Build**
   ```bash
   ./lab docker exec make -C projects/<name>
   ```

3. **Deploy to NFS rootfs**
   ```bash
   ./lab docker exec make -C projects/<name> deploy
   ```

4. **Load and verify**
   ```bash
   ./lab ssh -- insmod /lib/modules/<ver>/extra/<name>.ko
   ./lab ssh -- dmesg
   ```

## Files Touched
- `[CREATE]` `projects/<name>/Makefile`, `projects/<name>/<name>.c`

## Notes
Template source: [kmod_project](../../shared/templates/kmod_project/Makefile).
