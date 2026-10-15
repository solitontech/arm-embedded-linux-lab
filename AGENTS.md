# ARM Embedded Linux Lab — Agent Principles

This is a professional embedded Linux monorepo supporting multiple projects and hardware targets.

**Design for reuse:** Any code, script, or configuration that could serve more than one project belongs in `shared/`. Projects should consume shared resources, not duplicate them.

**Design for scale:** Never couple a script, tool, or library to a specific project or hardware board. Use variables and profiles so the same infrastructure can target any controller.

**Separate concerns cleanly:** Each top-level directory has a single purpose — respect those boundaries. Don't put infrastructure in project space. Don't put application logic in shared space.

**Generic OS/Cross-platform Support:** Always consider Windows, macOS, and Linux when developing generic approaches or infrastructure. Scripts and workflows should ideally support all OS environments. Avoid hardcoding OS-specific paths (like `/Volumes/bootfs` for macOS) when a cross-platform solution (e.g. dynamic mount detection) is possible.

## Network Services Are Docker-Only

**TFTP and NFS are served exclusively from the Docker container — never from the host directly.**

- `tftpd-hpa` (port 69) serves all boot files: `start4.elf`, `fixup4.dat`, `config.txt`, `u-boot.bin`, `boot.scr`, `Image`, DTB
- `nfs-kernel-server` (port 2049) exports the root filesystem at `/workspace/nfs/rpi4-rootfs/`
- `dnsmasq` (port 67) provides DHCP for network boot (EEPROM stage)

**Before any agent task involving network boot, TFTP, or NFS rootfs:**
1. Always check Docker is running: `./lab docker status` or `docker ps | grep arm-lab-dev`
2. If not running, start it: `./lab docker run` (auto-detects board profile for HOST_INTERFACE/HOST_IP)
3. Verify TFTP files are present: `./lab docker exec ls /workspace/tftp/`

**This applies to:**
- EEPROM netboot (Pi fetches `start4.elf` via TFTP from Docker)
- U-Boot TFTP boot (Pi fetches `Image` + DTB via TFTP from Docker)
- NFS rootfs mount (Pi mounts root over NFS from Docker)
- `lab_docker_exec` MCP tool calls (require the container to be up)

## Docker Development Environment

**Always use `./lab docker` to control the container — never call `./tools/docker/run.sh` or raw `docker` commands directly.**

The `lab` CLI is the single authoritative interface for Docker management:

| Command | Purpose |
|---|---|
| `./lab docker run` | Start the container (reads HOST_INTERFACE/HOST_IP from board profile) |
| `./lab docker run --board rpi4` | Start with explicit board profile |
| `./lab docker build` | Rebuild the Docker image |
| `./lab docker stop` | Stop the container |
| `./lab docker attach` | Attach to running container shell |
| `./lab docker exec <cmd>` | Run a single command inside the container |

This ensures HOST_INTERFACE and HOST_IP are always correctly injected from the board profile, so dnsmasq starts with the right network interface.

## README Principles

**Keep `README.md` concise, high-level, and clean.**
- Never duplicate multi-step operational procedures, granular terminal commands, or setup walkthroughs in `README.md`.
- Always delegate task-specific workflows to their corresponding **Skill** (`.agents/skills/`) or **Workflow** (`.agents/workflows/`).
- `README.md` should serve only as a welcoming entry point with high-level summaries and direct links to the relevant skills/workflows.

## Documentation & Relative Linking Standards

**Always use relative links in repository documentation (`.md` files):**
- Never commit absolute filesystem URIs (e.g. `file:///...` or hardcoded host paths like `/Users/...` or `/home/...`) in committed markdown documentation, READMEs, skills, or workflows.
- All internal links between documentation files, code files, and projects must use relative markdown paths (e.g. `[guide](boot_architecture.md)` or `[rpi4.mk](../../shared/build_system/boards/rpi4.mk)`).
- This ensures documentation renders and navigates correctly across all developer workstations, Docker containers, CI/CD, and GitHub.

**Strict Dependency Direction (Docs vs Projects):**
- **`docs/` must NEVER link to specific `projects/`:** Documentation in `docs/` and infrastructure in `shared/` are generic, board-level, or curriculum-wide assets. Linking from `docs/` to specific projects violates clean separation of concerns and breaks portability.
- **Projects link to docs, never the reverse:** Projects consume `docs/`, `shared/`, and `tools/`. A project README may link to any document in `docs/`, but files in `docs/` must remain completely decoupled from specific projects.

## Git Rules

**Never push to a remote.** Do not run `git push` under any circumstances unless the user explicitly asks you to. Commits are local only until the user decides to push.

## How to Operate in This Repo

Before starting any task, check `.agents/workflows/` for a workflow matching your task. If one exists, follow it. If not, complete your task and create a new workflow using `.agents/workflows/WORKFLOW_TEMPLATE.md` so future agents can benefit.

For reusable atomic operations (e.g., cross-compiling, deploying to a board), check `.agents/skills/` first. Create new skills using `.agents/skills/SKILL_TEMPLATE.md`.

## Skill & Workflow Maintenance Contract

**This is a hard rule that applies to every skill and workflow in this repo.**
Whenever any infrastructure file changes, the corresponding skill and/or workflow documentation must be updated in the same commit or task. No gap is acceptable.

**Crucially, while creating scalable or infra-level architectures (e.g., U-Boot builds, deploy scripts, cross-platform helpers), always ensure you add a skill or workflow so that a new agent can pick it up and use it.**

> **Do NOT duplicate this rule inside individual skill files.** This section in `AGENTS.md` is the single authoritative reminder. Skill files should stay focused on their instructions only.

| Infrastructure file changed | Documentation to update |
|---|---|
| `tools/lab.py` (new commands, renamed flags) | `.agents/skills/deploy-and-run/SKILL.md` |
| `Makefile` (new top-level targets) | `.agents/skills/deploy-and-run/SKILL.md` |
| `tools/target/*.sh` (deploy/reboot strategies) | `.agents/skills/deploy-and-run/SKILL.md` |
| `shared/build_system/boards/*.mk` (new board) | `.agents/workflows/new_board.md` |
| Docker infrastructure (`tools/docker/`) | `.agents/skills/docker-setup/SKILL.md` |
| MCP server (`tools/mcp/`) | `.agents/skills/lab-mcp/SKILL.md` |
| `tools/lab.py` (`mcp` subcommand) | `.agents/skills/deploy-and-run/SKILL.md` |
| New project scaffold template | `.agents/workflows/new_project.md` |
| EEPROM tooling (`tools/eeprom/`) | `.agents/skills/eeprom-netboot/SKILL.md` |

If you create a new infrastructure file or tool, also create a new skill or workflow documenting it.

## Primary CLI: `lab`

Always prefer `./lab <command>` over raw `make` calls when building, deploying, running, or rebooting. The `lab` CLI is the single authoritative interface for all agent and developer tasks. Raw `make` is an implementation detail.

Available commands: `list`, `new`, `info`, `build`, `clean`, `deploy`, `run`, `reboot`, `console`, `ssh`, `docker`, `gdb`, `doctor`, `mcp`, `completion`.

## Docker Development Environment

For cross-compilation on a fresh workstation (any OS), use the Docker environment:
- **Skill:** `.agents/skills/docker-setup/SKILL.md`
- **Workflow:** `.agents/workflows/docker_setup.md`
- **Docker CLI:** `./lab docker run | build | stop | exec <cmd> | status`

## MCP Server (Hardware Tool Bridge)

For AI agent access to physical boards (serial console, boot analysis, BSP management, bench verification):
- **Skill:** `.agents/skills/lab-mcp/SKILL.md`
- **Workflow:** `.agents/workflows/mcp_setup.md`
- **CLI:** `./lab mcp setup | start | stop | status | logs`
- **Config:** `.devin/config.json` (MCP client configuration)
