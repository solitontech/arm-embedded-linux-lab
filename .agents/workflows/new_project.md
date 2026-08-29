---
description: how to add a new project to the monorepo
---

# Add a New Project

## When to Use This Workflow
Use this workflow whenever a new embedded application project is being added to the monorepo under `projects/`.

## Prerequisites
- At least one board profile exists under `tools/deploy/boards/`
- DevContainer is running with the cross-compile toolchain available

## Steps

1. **Copy the project scaffold**
   ```bash
   cp -r shared/templates/new_project projects/<your-project-name>
   ```

2. **Set the project name in the Makefile**
   Open `projects/<your-project-name>/Makefile` and update `PROJECT_NAME`.

3. **Write your application code**
   Replace `src/main.cpp` with your daemon or application entry point.

4. **Set BOARD_OPT_FLAGS for your target hardware**
   Before building, export the CPU flag matching your board:
   ```bash
   export BOARD_OPT_FLAGS=-mcpu=cortex-a72   # Raspberry Pi 4
   export BOARD=-rpi4
   make
   ```

5. **Add to CODEOWNERS**
   Add a line for your project directory in `.github/CODEOWNERS`:
   ```
   /projects/<your-project-name>/   @solitontech/<your-team>
   ```

6. **Verify**
   Confirm a cross-compiled binary exists at `projects/<your-project-name>/build/<board>/<project-name>` and is an AArch64 ELF:
   ```bash
   file projects/<your-project-name>/build/<board>/<project-name>
   ```

## Files Touched
- `[CREATE]` `projects/<your-project-name>/` (copied from `shared/templates/new_project/`)
- `[MODIFY]` `projects/<your-project-name>/Makefile` — set `PROJECT_NAME`
- `[MODIFY]` `.github/CODEOWNERS` — add project ownership line

## Notes
- Never put build artifacts (`build/`) in version control — they are covered by `.gitignore`.
- If your project targets a new hardware board not yet in `tools/deploy/boards/`, run the `new_board` workflow first.
