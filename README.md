# ARM Embedded Linux Lab 🤼

Welcome to the **ARM Embedded Linux Lab** – the central repo and workspace for the Soliton Embedded Crew!

This repository contains our learning tracks, shared build tools, scripts, and experimental projects. From bare-metal ARM bring-up to custom Embedded Linux platforms, this is where we collaborate, build, and occasionally debug kernel panics together.

## 📁 Repository Structure

* docs/ - Contains our markdown learning tracks, architecture references, and setup guides.
* tools/ - Shared scripts for cross-compilation toolchains, QEMU runners, and hardware deployment etc.
* shared/ - Reusable C/C++ libraries, device tree overlays, and custom Buildroot / Yocto layers etc.
* projects/ - Active project workspaces and platform implementations.
* scratchpad/ - A sandbox for team members to push small tests, standalone drivers, and experiments.

## 🚀 Getting Started

1. **Clone the repository:**
   ```bash
   git clone <repo-url>
   cd arm-embedded-linux-lab
   ```

2. **Workspace Setup:**
   Follow setup guides in docs/ to configure your development environment.

   **Option A — Docker (recommended for any OS):**
   ```bash
   ./tools/docker/run.sh install-docker # installs Docker on host if not present
   ./tools/docker/run.sh build          # build the image once
   ./tools/docker/run.sh run            # enter container (repo mounted at /workspace)
   ./lab doctor                         # verify toolchains inside container
   ```
   See [`.agents/skills/docker-setup/SKILL.md`](.agents/skills/docker-setup/SKILL.md) for full details.

   **Option B — Native install:**
   Install cross-compilers and tools manually, then run `./lab doctor` to verify.

3. **Build a project:**
   ```bash
   ./lab new hello --type app --board rpi4   # scaffold
   ./lab build hello --board rpi4            # compile
   ./lab deploy hello --board rpi4 --dry-run # preview deployment
   ```

4. **Explore available commands:**
   ```bash
   ./lab --help
   ./lab list
   ```

---
*Maintained by Soliton Embedded Crew. All skill levels welcome. Let the wrestling begin. 💪*
