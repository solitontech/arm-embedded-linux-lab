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

1. **Workspace Setup:**
   - **Docker Setup (recommended for any OS):** Follow the [`docker-setup` Skill](.agents/skills/docker-setup/SKILL.md) / [Workflow](.agents/workflows/docker_setup.md) to set up and run the containerized development environment.
   - **Native Setup:** Install toolchains natively and run `./lab doctor` to verify environment health.

2. **Core Development Workflow:**
   - **Primary CLI:** Use `./lab <command>` for all tasks. See available commands with `./lab list` or `./lab --help`.
   - **Creating Projects:** Follow the [New Project Workflow](.agents/workflows/new_project.md).
   - **Building & Deploying:** Follow the [Deploy and Run Skill](.agents/skills/deploy-and-run/SKILL.md).

---
*Maintained by Soliton Embedded Crew. All skill levels welcome. Let the wrestling begin. 💪*
