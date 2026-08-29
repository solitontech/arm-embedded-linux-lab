#!/usr/bin/env python3
"""
==============================================================================
lab — Unified Python Task Runner for ARM Embedded Linux Lab Monorepo
==============================================================================
Provides interactive, rich task execution for building, deploying, running,
rebooting, and diagnosing projects and target boards.
"""

import sys
import os
import re
import shutil
import subprocess
import argparse
import socket
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

# ------------------------------------------------------------------------------
# Terminal Aesthetics & Formatting
# ------------------------------------------------------------------------------
class Style:
    RESET   = "\033[0m"
    BOLD    = "\033[1m"
    DIM     = "\033[2m"
    
    # Foreground
    RED     = "\033[31m"
    GREEN   = "\033[32m"
    YELLOW  = "\033[33m"
    BLUE    = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN    = "\033[36m"
    WHITE   = "\033[37m"
    
    # Bright Foreground
    B_RED   = "\033[91m"
    B_GREEN = "\033[92m"
    B_YELLOW= "\033[93m"
    B_BLUE  = "\033[94m"
    B_CYAN  = "\033[96m"

def cprint(color: str, text: str, bold: bool = False, end: str = "\n"):
    prefix = Style.BOLD if bold else ""
    print(f"{prefix}{color}{text}{Style.RESET}", end=end)

def log_info(msg: str):
    print(f"{Style.BOLD}{Style.B_BLUE}❯ [INFO]{Style.RESET} {msg}")

def log_success(msg: str):
    print(f"{Style.BOLD}{Style.B_GREEN}✔ [SUCCESS]{Style.RESET} {msg}")

def log_warn(msg: str):
    print(f"{Style.BOLD}{Style.B_YELLOW}⚠ [WARN]{Style.RESET} {msg}")

def log_error(msg: str):
    print(f"{Style.BOLD}{Style.B_RED}✖ [ERROR]{Style.RESET} {msg}", file=sys.stderr)

def print_banner():
    banner = f"""{Style.BOLD}{Style.B_CYAN}
 ╔═══════════════════════════════════════════════════════════════════════╗
 ║              ARM EMBEDDED LINUX LAB — TASK RUNNER                    ║
 ╚═══════════════════════════════════════════════════════════════════════╝{Style.RESET}"""
    print(banner)

# ------------------------------------------------------------------------------
# Repository Context & Discovery
# ------------------------------------------------------------------------------
def find_repo_root() -> Path:
    current = Path(__file__).resolve().parent
    while current != current.parent:
        if (current / "shared" / "build_system" / "framework.mk").exists():
            return current
        current = current.parent
    # Fallback to current working directory
    return Path.cwd()

REPO_ROOT = find_repo_root()

def get_boards() -> Dict[str, Dict[str, str]]:
    boards_dir = REPO_ROOT / "shared" / "build_system" / "boards"
    boards = {}
    if not boards_dir.exists():
        return boards
    
    for mk_file in sorted(boards_dir.glob("*.mk")):
        board_name = mk_file.stem
        info = {
            "name": board_name,
            "desc": board_name,
            "arch": "unknown",
            "cross": "",
            "default_deploy": "ssh"
        }
        with open(mk_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith("BOARD_DESC"):
                    info["desc"] = line.split(":=", 1)[-1].strip().strip('"')
                elif line.startswith("ARCH"):
                    info["arch"] = line.split(":=", 1)[-1].strip().strip('"')
                elif line.startswith("CROSS_COMPILE"):
                    info["cross"] = line.split("?=", 1)[-1].split(":=", 1)[-1].strip()
                elif line.startswith("DEFAULT_DEPLOY"):
                    info["default_deploy"] = line.split(":=", 1)[-1].strip()
        boards[board_name] = info
    return boards

def get_board_env(board_name: str) -> Dict[str, str]:
    env_file = REPO_ROOT / "tools" / "deploy" / "boards" / f"{board_name}.env"
    example_file = REPO_ROOT / "tools" / "deploy" / "boards" / f"{board_name}.env.example"
    
    target_file = env_file if env_file.exists() else (example_file if example_file.exists() else None)
    data = {}
    if target_file:
        with open(target_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    data[k.strip()] = v.strip().strip('"').strip("'")
    return data

def get_projects() -> Dict[str, Dict[str, Any]]:
    projects_dir = REPO_ROOT / "projects"
    projects = {}
    if not projects_dir.exists():
        return projects
    
    for p_dir in sorted(projects_dir.iterdir()):
        mk_file = p_dir / "Makefile"
        if p_dir.is_dir() and mk_file.exists():
            proj_name = p_dir.name
            info = {
                "name": proj_name,
                "path": p_dir,
                "type": "app",
                "default_board": "rpi4",
                "deploy_method": "ssh",
                "target_dest": "/usr/local/bin"
            }
            with open(mk_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("PROJECT_TYPE"):
                        info["type"] = line.split(":=", 1)[-1].strip()
                    elif line.startswith("DEFAULT_BOARD"):
                        info["default_board"] = line.split(":=", 1)[-1].strip()
                    elif line.startswith("DEPLOY_METHOD"):
                        info["deploy_method"] = line.split(":=", 1)[-1].strip()
                    elif line.startswith("TARGET_DEST_DIR"):
                        info["target_dest"] = line.split(":=", 1)[-1].strip()
            projects[proj_name] = info
    return projects

def select_project(user_choice: Optional[str] = None) -> str:
    projects = get_projects()
    if not projects:
        log_error("No projects found under projects/. Create one with 'lab new <name>'.")
        sys.exit(1)
    
    if user_choice:
        if user_choice in projects:
            return user_choice
        log_error(f"Project '{user_choice}' not found. Available: {', '.join(projects.keys())}")
        sys.exit(1)
    
    if len(projects) == 1:
        return list(projects.keys())[0]
    
    # Interactive selection if connected to TTY
    if sys.stdin.isatty():
        print(f"\n{Style.BOLD}Select a Project:{Style.RESET}")
        p_list = list(projects.keys())
        for idx, p in enumerate(p_list, 1):
            p_info = projects[p]
            print(f"  [{Style.B_CYAN}{idx}{Style.RESET}] {Style.BOLD}{p:<20}{Style.RESET} ({p_info['type']}, default board: {p_info['default_board']})")
        
        while True:
            try:
                choice = input(f"{Style.BOLD}Enter number (1-{len(p_list)}) [1]: {Style.RESET}").strip()
                if not choice:
                    return p_list[0]
                num = int(choice)
                if 1 <= num <= len(p_list):
                    return p_list[num - 1]
            except (ValueError, KeyboardInterrupt):
                print()
                sys.exit(0)
    else:
        return list(projects.keys())[0]

def select_board(project_name: Optional[str] = None, user_board: Optional[str] = None) -> str:
    boards = get_boards()
    if user_board:
        if user_board in boards:
            return user_board
        log_error(f"Board '{user_board}' not recognized. Available: {', '.join(boards.keys())}")
        sys.exit(1)
    
    if project_name:
        projects = get_projects()
        if project_name in projects:
            default_b = projects[project_name].get("default_board", "rpi4")
            if default_b in boards:
                return default_b
    return "rpi4" if "rpi4" in boards else (list(boards.keys())[0] if boards else "host")

# ------------------------------------------------------------------------------
# Subcommand Handlers
# ------------------------------------------------------------------------------
def cmd_list(args: argparse.Namespace):
    print_banner()
    boards = get_boards()
    projects = get_projects()
    
    # Boards Table
    print(f"\n{Style.BOLD}{Style.B_BLUE}▶ SUPPORTED HARDWARE BOARDS ({len(boards)}){Style.RESET}")
    print(f"{Style.DIM}─" * 72 + f"{Style.RESET}")
    print(f" {Style.BOLD}{'BOARD':<14} {'ARCH':<10} {'DEFAULT DEPLOY':<16} {'DESCRIPTION'}{Style.RESET}")
    print(f"{Style.DIM}─" * 72 + f"{Style.RESET}")
    for b_name, b_info in boards.items():
        env = get_board_env(b_name)
        ip_status = f" (IP: {env.get('TARGET_IP')})" if env.get("TARGET_IP") else ""
        print(f" {Style.B_CYAN}{b_name:<14}{Style.RESET} {b_info['arch']:<10} {b_info['default_deploy']:<16} {b_info['desc']}{Style.DIM}{ip_status}{Style.RESET}")
    print(f"{Style.DIM}─" * 72 + f"{Style.RESET}")

    # Projects Table
    print(f"\n{Style.BOLD}{Style.B_GREEN}▶ ACTIVE MONOREPO PROJECTS ({len(projects)}){Style.RESET}")
    print(f"{Style.DIM}─" * 72 + f"{Style.RESET}")
    if not projects:
        print(f"  {Style.DIM}(No projects found. Create one with 'lab new <project_name>'){Style.RESET}")
    else:
        print(f" {Style.BOLD}{'PROJECT':<20} {'TYPE':<12} {'DEFAULT BOARD':<16} {'DEPLOY METHOD'}{Style.RESET}")
        print(f"{Style.DIM}─" * 72 + f"{Style.RESET}")
        for p_name, p_info in projects.items():
            print(f" {Style.BOLD}{p_name:<20}{Style.RESET} {p_info['type']:<12} {p_info['default_board']:<16} {p_info['deploy_method']}")
    print(f"{Style.DIM}─" * 72 + f"{Style.RESET}\n")

def cmd_new(args: argparse.Namespace):
    proj_name = args.name.strip()
    proj_dir = REPO_ROOT / "projects" / proj_name
    template_dir = REPO_ROOT / "shared" / "templates" / "new_project"
    
    if proj_dir.exists():
        log_error(f"Project directory '{proj_dir}' already exists.")
        sys.exit(1)
    
    if not template_dir.exists():
        log_error(f"Scaffolding template '{template_dir}' not found.")
        sys.exit(1)
    
    log_info(f"Scaffolding new project: {Style.BOLD}{proj_name}{Style.RESET} ({args.type})...")
    shutil.copytree(template_dir, proj_dir)
    
    # Customize Makefile
    mk_path = proj_dir / "Makefile"
    if mk_path.exists():
        content = mk_path.read_text(encoding="utf-8")
        content = content.replace("PROJECT_NAME    := my-project", f"PROJECT_NAME    := {proj_name}")
        content = content.replace("PROJECT_TYPE    := app", f"PROJECT_TYPE    := {args.type}")
        if args.board:
            content = content.replace("DEFAULT_BOARD   := rpi4", f"DEFAULT_BOARD   := {args.board}")
        mk_path.write_text(content, encoding="utf-8")
    
    log_success(f"Project created at {Style.BOLD}projects/{proj_name}/{Style.RESET}")
    print(f"\nQuick Start Commands:")
    print(f"  {Style.B_CYAN}lab build {proj_name}{Style.RESET}")
    print(f"  {Style.B_CYAN}lab info {proj_name}{Style.RESET}")
    print(f"  {Style.B_CYAN}lab deploy {proj_name}{Style.RESET}\n")

def cmd_info(args: argparse.Namespace):
    proj_name = select_project(args.project)
    board = select_board(proj_name, args.board)
    proj_dir = REPO_ROOT / "projects" / proj_name
    
    cmd = ["make", "-C", str(proj_dir), "info", f"BOARD={board}"]
    subprocess.run(cmd)

def cmd_build(args: argparse.Namespace):
    if args.all:
        projects = get_projects()
        board = select_board(None, args.board)
        log_info(f"Building ALL ({len(projects)}) projects for board: {Style.BOLD}{board}{Style.RESET}")
        for p in projects:
            proj_dir = REPO_ROOT / "projects" / p
            log_info(f"--> Building {p}...")
            res = subprocess.run(["make", "-C", str(proj_dir), f"BOARD={board}"])
            if res.returncode != 0:
                log_error(f"Build failed for project: {p}")
                sys.exit(res.returncode)
        log_success("All projects built successfully.")
        return

    proj_name = select_project(args.project)
    board = select_board(proj_name, args.board)
    proj_dir = REPO_ROOT / "projects" / proj_name
    
    if args.clean:
        log_info(f"Cleaning previous build for {board}...")
        subprocess.run(["make", "-C", str(proj_dir), "clean", f"BOARD={board}"])
    
    log_info(f"Building {Style.BOLD}{proj_name}{Style.RESET} for board: {Style.BOLD}{board}{Style.RESET}...")
    res = subprocess.run(["make", "-C", str(proj_dir), f"BOARD={board}"])
    if res.returncode == 0:
        log_success(f"Build finished for {proj_name} ({board})")
    else:
        sys.exit(res.returncode)

def cmd_clean(args: argparse.Namespace):
    if args.distclean:
        log_info("Running distclean across monorepo...")
        subprocess.run(["make", "distclean"], cwd=REPO_ROOT)
        log_success("All build directories removed.")
        return

    proj_name = select_project(args.project)
    board = select_board(proj_name, args.board)
    proj_dir = REPO_ROOT / "projects" / proj_name
    subprocess.run(["make", "-C", str(proj_dir), "clean", f"BOARD={board}"])

def cmd_deploy(args: argparse.Namespace):
    proj_name = select_project(args.project)
    board = select_board(proj_name, args.board)
    proj_dir = REPO_ROOT / "projects" / proj_name
    
    cmd = ["make", "-C", str(proj_dir), "deploy", f"BOARD={board}"]
    if args.method:
        cmd.append(f"DEPLOY_METHOD={args.method}")
    
    if args.dry_run:
        # Direct dry run invocation of deploy.sh
        info = get_projects().get(proj_name, {})
        env = get_board_env(board)
        deploy_script = REPO_ROOT / "tools" / "deploy" / "deploy.sh"
        target_file = proj_dir / "build" / board / proj_name
        
        log_info(f"Executing DRY-RUN deployment for {proj_name} -> {board}...")
        subprocess.run([
            str(deploy_script),
            f"--board={board}",
            f"--method={args.method or info.get('deploy_method', 'ssh')}",
            f"--files={target_file}",
            f"--target-ip={env.get('TARGET_IP', '')}",
            "--dry-run"
        ])
        return

    res = subprocess.run(cmd)
    if res.returncode != 0:
        sys.exit(res.returncode)

def cmd_run(args: argparse.Namespace):
    proj_name = select_project(args.project)
    board = select_board(proj_name, args.board)
    proj_dir = REPO_ROOT / "projects" / proj_name
    
    # For the host board, run the binary directly after ensuring it is built
    if board == "host":
        # Ensure the binary is built
        build_cmd = ["make", "-C", str(proj_dir), f"BOARD={board}"]
        res = subprocess.run(build_cmd)
        if res.returncode != 0:
            sys.exit(res.returncode)
        binary_path = proj_dir / "build" / board / proj_name
        if not binary_path.exists():
            log_error(f"Binary {binary_path} not found after build.")
            sys.exit(1)
        log_info(f"Executing {binary_path} locally on host.")
        subprocess.run([str(binary_path)])
        return
    
    # Default behavior for non‑host boards
    cmd = ["make", "-C", str(proj_dir), "run", f"BOARD={board}"]
    subprocess.run(cmd)

def cmd_reboot(args: argparse.Namespace):
    board = select_board(None, args.board)
    env = get_board_env(board)
    reboot_script = REPO_ROOT / "tools" / "deploy" / "reboot.sh"
    
    method = args.method or env.get("BOARD_RESET_METHOD", "uboot_serial")
    
    cmd = [
        str(reboot_script),
        f"--board={board}",
        f"--method={method}",
        f"--serial-port={env.get('BOARD_SERIAL_PORT', '')}",
        f"--serial-baud={env.get('BOARD_SERIAL_BAUD', '115200')}",
        f"--reset-cmd={env.get('BOARD_RESET_CMD', 'reset\\r')}",
        f"--target-ip={env.get('TARGET_IP', '')}",
        f"--target-user={env.get('TARGET_USER', 'root')}"
    ]
    if args.dry_run:
        cmd.append("--dry-run")
    
    subprocess.run(cmd)

def cmd_console(args: argparse.Namespace):
    board = select_board(None, args.board)
    env = get_board_env(board)
    console_script = REPO_ROOT / "tools" / "deploy" / "console.sh"
    
    cmd = [
        str(console_script),
        f"--board={board}",
        f"--serial-port={env.get('BOARD_SERIAL_PORT', '')}",
        f"--serial-baud={env.get('BOARD_SERIAL_BAUD', '115200')}"
    ]
    subprocess.run(cmd)

def cmd_gdb(args: argparse.Namespace):
    proj_name = select_project(args.project)
    board = select_board(proj_name, args.board)
    proj_dir = REPO_ROOT / "projects" / proj_name
    target_elf = proj_dir / "build" / board / proj_name
    
    if not target_elf.exists():
        log_warn(f"Binary {target_elf} not found. Building first...")
        subprocess.run(["make", "-C", str(proj_dir), f"BOARD={board}"])
    
    env = get_board_env(board)
    gdb_script = REPO_ROOT / "tools" / "deploy" / "gdb.sh"
    
    cmd = [
        str(gdb_script),
        f"--target-elf={target_elf}",
        f"--target-ip={env.get('TARGET_IP', '')}",
        f"--gdb-port={args.port or env.get('GDB_PORT', '2345')}"
    ]
    subprocess.run(cmd)

def cmd_doctor(args: argparse.Namespace):
    print_banner()
    print(f"{Style.BOLD}{Style.B_BLUE}▶ RUNNING ENVIRONMENT & LAB DIAGNOSTICS{Style.RESET}\n")
    
    # 1. Check Toolchains
    print(f"{Style.BOLD}1. Compiler Toolchains:{Style.RESET}")
    toolchains = [
        ("aarch64-linux-gnu-gcc", "ARM64 Cross Compiler (RPi4, RPi3, QEMU)"),
        ("arm-linux-gnueabihf-gcc", "ARM32 Cross Compiler (BeagleBone Black)"),
        ("gcc", "Host Native C Compiler"),
        ("g++", "Host Native C++ Compiler"),
        ("clang++", "LLVM / Clang C++ Compiler"),
    ]
    for bin_name, desc in toolchains:
        path = shutil.which(bin_name)
        if path:
            print(f"  {Style.B_GREEN}✔{Style.RESET} {bin_name:<26} -> {Style.DIM}{path}{Style.RESET}")
        else:
            print(f"  {Style.B_YELLOW}⚠{Style.RESET} {bin_name:<26} -> {Style.DIM}Not installed ({desc}){Style.RESET}")

    # 2. Check Terminal & Debug Tools
    print(f"\n{Style.BOLD}2. Serial & Debugging Tools:{Style.RESET}")
    tools = [
        ("gdb-multiarch", "Multi-architecture GDB Client"),
        ("gdb", "Standard GDB Client"),
        ("picocom", "Minimal Serial Terminal Emulator"),
        ("minicom", "Full Serial Communication Program"),
        ("rsync", "Fast Remote File Sync"),
        ("scp", "Secure Copy Protocol"),
        ("ssh", "Secure Shell Client"),
    ]
    for bin_name, desc in tools:
        path = shutil.which(bin_name)
        if path:
            print(f"  {Style.B_GREEN}✔{Style.RESET} {bin_name:<26} -> {Style.DIM}{path}{Style.RESET}")
        else:
            print(f"  {Style.B_YELLOW}⚠{Style.RESET} {bin_name:<26} -> {Style.DIM}Not installed ({desc}){Style.RESET}")

    # 3. Detect Connected USB Serial Adapters
    print(f"\n{Style.BOLD}3. Detected Host Serial Ports:{Style.RESET}")
    dev_patterns = ["/dev/ttyUSB*", "/dev/ttyACM*", "/dev/cu.usb*", "/dev/cu.SLAB*"]
    found_devices = []
    for pat in dev_patterns:
        found_devices.extend(Path("/dev").glob(pat.split("/")[-1]))
    
    if found_devices:
        for d in found_devices:
            print(f"  {Style.B_GREEN}✔{Style.RESET} Attached Port: {Style.B_CYAN}{d}{Style.RESET}")
    else:
        print(f"  {Style.DIM}No USB-to-UART serial adapters detected in /dev/{Style.RESET}")

    # 4. Lab Boards Reachability Check
    print(f"\n{Style.BOLD}4. Lab Board Network Status:{Style.RESET}")
    boards = get_boards()
    for b_name in boards:
        env = get_board_env(b_name)
        ip = env.get("TARGET_IP")
        if ip and ip != "127.0.0.1":
            # Quick ping/port check
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(0.6)
            try:
                s.connect((ip, int(env.get("TARGET_PORT", 22))))
                s.close()
                print(f"  {Style.B_GREEN}✔{Style.RESET} [{b_name:<10}] {ip:<15} -> {Style.B_GREEN}Online (SSH Reachable){Style.RESET}")
            except Exception:
                print(f"  {Style.B_RED}✖{Style.RESET} [{b_name:<10}] {ip:<15} -> {Style.DIM}Offline / Unreachable{Style.RESET}")
        elif ip == "127.0.0.1":
            print(f"  {Style.B_GREEN}✔{Style.RESET} [{b_name:<10}] {ip:<15} -> {Style.DIM}Local Loopback{Style.RESET}")
        else:
            print(f"  {Style.DIM}• [{b_name:<10}] <IP not configured in tools/deploy/boards/{b_name}.env>{Style.RESET}")

    print(f"\n{Style.BOLD}{Style.B_GREEN}Diagnostics complete.{Style.RESET}\n")

def cmd_completion(args: argparse.Namespace):
    shell = args.shell or "zsh"
    projects = " ".join(get_projects().keys())
    boards = " ".join(get_boards().keys())
    
    if shell == "bash":
        script = f"""# Bash completion for lab
_lab_complete() {{
    local cur prev words cword
    _init_completion || return

    local commands="list new info build clean deploy run reboot console gdb doctor completion"
    local boards="{boards}"
    local projects="{projects}"

    case "$prev" in
        new)
            return 0
            ;;
        info|build|clean|deploy|run|gdb)
            COMPREPLY=( $(compgen -W "$projects" -- "$cur") )
            return 0
            ;;
        --board)
            COMPREPLY=( $(compgen -W "$boards" -- "$cur") )
            return 0
            ;;
        --type)
            COMPREPLY=( $(compgen -W "app lib_static lib_shared" -- "$cur") )
            return 0
            ;;
    esac

    if [[ "$cur" == -* ]]; then
        COMPREPLY=( $(compgen -W "--board --clean --all --dry-run --method --type --port" -- "$cur") )
    else
        COMPREPLY=( $(compgen -W "$commands" -- "$cur") )
    fi
}}
complete -F _lab_complete lab ./lab
"""
    else:
        script = f"""#compdef lab ./lab

_lab() {{
    local -a commands
    commands=(
        'list:List all projects and hardware boards'
        'new:Scaffold a new project'
        'info:Display resolved configuration'
        'build:Compile project(s)'
        'clean:Clean build artifacts'
        'deploy:Deploy artifacts to target'
        'run:Deploy and execute on target'
        'reboot:Reset/reboot target hardware'
        'console:Connect to serial UART console'
        'gdb:Start remote GDB session'
        'doctor:Diagnose toolchains and lab environment'
        'completion:Generate shell completion script'
    )

    local -a projects=({projects})
    local -a boards=({boards})

    _arguments -C \\
        '1: :->command' \\
        '*: :->args'

    case $state in
        command)
            _describe -t commands 'lab command' commands
            ;;
        args)
            case $words[2] in
                info|build|clean|deploy|run|gdb)
                    _values 'projects' $projects
                    ;;
                reboot|console)
                    _arguments '--board=[Target board]:board:($boards)'
                    ;;
            esac
            ;;
    esac
}}

_lab "$@"
"""
    print(script)

# ------------------------------------------------------------------------------
# CLI Parser Definition
# ------------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        prog="lab",
        description="Unified Task Runner for ARM Embedded Linux Lab monorepo.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # list
    p_list = subparsers.add_parser("list", aliases=["ls"], help="List all projects and board profiles")
    p_list.set_defaults(func=cmd_list)

    # new
    p_new = subparsers.add_parser("new", help="Scaffold a new project")
    p_new.add_argument("name", help="Name of the new project")
    p_new.add_argument("--type", choices=["app", "lib_static", "lib_shared"], default="app", help="Project type")
    p_new.add_argument("--board", help="Default target board (e.g. rpi4)")
    p_new.set_defaults(func=cmd_new)

    # info
    p_info = subparsers.add_parser("info", help="Inspect resolved project and board configuration")
    p_info.add_argument("project", nargs="?", help="Project name")
    p_info.add_argument("--board", help="Target hardware board")
    p_info.set_defaults(func=cmd_info)

    # build
    p_build = subparsers.add_parser("build", help="Build project(s)")
    p_build.add_argument("project", nargs="?", help="Project name (prompts if omitted)")
    p_build.add_argument("--board", help="Target hardware board (e.g. rpi4, rpi3, beaglebone, host)")
    p_build.add_argument("--clean", action="store_true", help="Clean prior to building")
    p_build.add_argument("--all", action="store_true", help="Build all projects in monorepo")
    p_build.set_defaults(func=cmd_build)

    # clean
    p_clean = subparsers.add_parser("clean", help="Clean build artifacts")
    p_clean.add_argument("project", nargs="?", help="Project name")
    p_clean.add_argument("--board", help="Target hardware board")
    p_clean.add_argument("--distclean", action="store_true", help="Clean all builds across monorepo")
    p_clean.set_defaults(func=cmd_clean)

    # deploy
    p_deploy = subparsers.add_parser("deploy", help="Deploy project artifacts to target")
    p_deploy.add_argument("project", nargs="?", help="Project name")
    p_deploy.add_argument("--board", help="Target hardware board")
    p_deploy.add_argument("--method", help="Deploy method (ssh, tftp, nfs)")
    p_deploy.add_argument("--dry-run", action="store_true", help="Simulate deployment without executing")
    p_deploy.set_defaults(func=cmd_deploy)

    # run
    p_run = subparsers.add_parser("run", help="Deploy and execute application on target")
    p_run.add_argument("project", nargs="?", help="Project name")
    p_run.add_argument("--board", help="Target hardware board")
    p_run.set_defaults(func=cmd_run)

    # reboot
    p_reboot = subparsers.add_parser("reboot", help="Trigger target board reset/reboot")
    p_reboot.add_argument("--board", help="Target hardware board")
    p_reboot.add_argument("--method", choices=["uboot_serial", "ssh", "sysrq_serial", "power_relay"], help="Reset strategy")
    p_reboot.add_argument("--dry-run", action="store_true", help="Simulate reset without sending commands")
    p_reboot.set_defaults(func=cmd_reboot)

    # console
    p_console = subparsers.add_parser("console", help="Connect to serial UART console")
    p_console.add_argument("--board", help="Target hardware board")
    p_console.set_defaults(func=cmd_console)

    # gdb
    p_gdb = subparsers.add_parser("gdb", help="Start cross-GDB remote debug session")
    p_gdb.add_argument("project", nargs="?", help="Project name")
    p_gdb.add_argument("--board", help="Target hardware board")
    p_gdb.add_argument("--port", help="Target gdbserver port (default: 2345)")
    p_gdb.set_defaults(func=cmd_gdb)

    # doctor
    p_doc = subparsers.add_parser("doctor", help="Diagnose toolchains, serial ports, and lab network")
    p_doc.set_defaults(func=cmd_doctor)

    # completion
    p_comp = subparsers.add_parser("completion", help="Generate shell auto-completion script")
    p_comp.add_argument("shell", choices=["bash", "zsh"], nargs="?", default="zsh")
    p_comp.set_defaults(func=cmd_completion)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    if hasattr(args, "func"):
        args.func(args)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[INFO] Operation aborted by user.")
        sys.exit(0)
