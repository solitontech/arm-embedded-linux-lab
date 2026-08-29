---
description: how to add a new project to the monorepo
---

# Add a New Project

## When to Use This Workflow
Use this workflow whenever a new embedded application or library is being added to the monorepo under `projects/`.

## Prerequisites
- Target board profile exists under `shared/build_system/boards/` (e.g. `rpi4`, `rpi3`, `beaglebone`, `qemu_arm64`, `host`)
- DevContainer or cross-compilation toolchain is available

## Steps

1. **Scaffold the project**
   From the repository root:
   ```bash
   make new-project NAME=<your-project-name>
   ```
   *Alternatively:*
   ```bash
   cp -r shared/templates/new_project projects/<your-project-name>
   ```

2. **Configure project metadata and requirements**
   Edit `projects/<your-project-name>/Makefile`:
   - `PROJECT_NAME` — Project name (defaults to folder name)
   - `PROJECT_TYPE` — `app` (executable), `lib_static` (`.a`), `lib_shared` (`.so`), or `raw`
   - `DEFAULT_BOARD` — Target hardware board (e.g. `rpi4`)
   - `DEPLOY_METHOD` — Preferred deployment strategy (`ssh`, `tftp`, `nfs`, or combinations)
   - `TARGET_DEST_DIR` — Destination directory on target (e.g. `/usr/local/bin`)
   - `CXXFLAGS_EXTRA` / `CFLAGS_EXTRA` / `LDLIBS_EXTRA` — Project-specific dependencies (e.g. `-lgpiod -lpthread`)

3. **Inspect resolved configuration**
   ```bash
   make -C projects/<your-project-name> info [BOARD=<target-board>]
   ```

4. **Write application code**
   Add or update source files in `src/` (e.g. `src/main.cpp`). Easymake automatically discovers all `.c`, `.cpp`, and `.s` files.

5. **Build and test**
   ```bash
   # Build for default board or specific board
   make -C projects/<your-project-name> BOARD=rpi4
   ```

6. **Deploy to hardware target**
   ```bash
   make -C projects/<your-project-name> deploy BOARD=rpi4
   ```

7. **Add to CODEOWNERS**
   Add ownership in `.github/CODEOWNERS`:
   ```
   /projects/<your-project-name>/   @solitontech/<your-team>
   ```

## Files Touched
- `[CREATE]` `projects/<your-project-name>/`
- `[MODIFY]` `projects/<your-project-name>/Makefile`
- `[MODIFY]` `.github/CODEOWNERS`
