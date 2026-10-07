---
name: deploy-and-run
description: Build, deploy, run, and reboot target boards across multiple hardware architectures and projects using the unified lab framework.
---

# Deploy and Run on Target Boards (`lab` CLI)

## Purpose
Enables automated building, cross-compilation, deployment (SSH, TFTP, NFS), and hardware control (reboot, console, GDB) for any project in the monorepo.

## Primary CLI Commands (`./lab`)

| Command | Usage Example | Description |
|---|---|---|
| `list` | `./lab list` | List all available projects and target board profiles |
| `new` | `./lab new myapp --type app --board rpi4` | Scaffold a new project (`app`, `lib_static`, `lib_shared`) |
| `info` | `./lab info myapp --board rpi4` | Display resolved build flags, toolchains, and deploy settings |
| `build` | `./lab build myapp --board rpi4` | Cross-compile project for target board (`--clean`, `--all`) |
| `clean` | `./lab clean myapp --board rpi4` | Clean build directory (`--distclean` to wipe all builds) |
| `deploy` | `./lab deploy myapp --board rpi4` | Transfer binary to target via SSH, TFTP, or NFS (`--dry-run`) |
| `run` | `./lab run myapp --board rpi4` | Deploy and execute binary remotely over SSH |
| `reboot` | `./lab reboot --board rpi4` | Reset target board via U-Boot serial, SSH, or power relay |
| `console` | `./lab console --board rpi4` | Connect to physical UART serial boot console |
| `ssh` | `./lab ssh --board rpi4` | SSH into the target board |
| `docker` | `./lab docker` | Enter the Docker development environment |
| `gdb` | `./lab gdb myapp --board rpi4` | Connect cross-gdb to target gdbserver session |
| `doctor` | `./lab doctor` | Run environment diagnostics inside Docker (toolchains, serial, TFTP, network) |
| `completion` | `./lab completion zsh >> ~/.zshrc` | Generate bash/zsh auto-completion script |

## Step-by-Step Workflow

### Step 1: Inspect Target Configuration
```bash
lab info <project-name> --board <board-name>
```

### Step 2: Build Project
```bash
lab build <project-name> --board <board-name>
```

### Step 3: Deploy to Board
```bash
lab deploy <project-name> --board <board-name>
```

### Step 4: Run Application Remotely
```bash
lab run <project-name> --board <board-name>
```

### Step 5: Serial Console & Debugging
```bash
lab console --board <board-name>
lab gdb <project-name> --board <board-name>
```

## Notes
- Use `./lab <command>` as the primary entry point for all operations.
- Dry-run mode (`--dry-run`) simulates actions without touching physical hardware or networks.
- All object files and binaries live in `projects/<project>/build/<board>/`.
