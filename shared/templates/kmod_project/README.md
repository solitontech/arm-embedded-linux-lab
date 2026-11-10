# Kernel module template

Copy to `projects/<name>`, rename `hello.c`, set `MODULE_NAME` in the Makefile.
Full procedure: [kernel module workflow](../../../.agents/workflows/new_kernel_module.md).

## Editor setup (IntelliSense)

Kernel include paths, defines and force-includes live in one shared config for all
modules: [`.vscode/c_cpp_properties.json`](../../../.vscode/c_cpp_properties.json) at the repo
root. Open the repo root in VS Code and nothing needs to be copied per module. It needs the
kernel build tree first (see the [kernel-module-dev skill](../../../.agents/skills/kernel-module-dev/SKILL.md)).
`KBUILD_MODNAME` there is a generic placeholder (only used by IntelliSense for `pr_fmt`).

For clangd instead: `./lab docker exec make -C projects/<name> compdb HOST_ROOT=<host repo path>`
(writes `build/<board>/compile_commands.json`; point clangd at it with `--compile-commands-dir`).

## Build output

Everything generated (`.o`, `.cmd`, `.mod*`, `Module.symvers`, `<name>.ko`) goes to
`build/<board>/` inside the project, which is git-ignored. The project folder only holds
your sources. `make clean` removes `build/<board>/`. For a multi-file module list the
sources in `MODULE_SRCS` in the Makefile.
