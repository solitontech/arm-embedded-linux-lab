# Kernel module template

Copy to `projects/<name>`, rename `hello.c`, set `MODULE_NAME` in the Makefile.
Full procedure: [kernel module workflow](../../../.agents/workflows/new_kernel_module.md).

## Editor setup (IntelliSense)

The template ships `.vscode/c_cpp_properties.json` with kernel include paths
(relative to the repo root, so open the repo root in VS Code, or copy the file to the
repo's `.vscode/`). It needs the kernel tree built first:
`./lab docker exec make -C shared/kernel BOARD=rpi4 build modules-prepare`.
`KBUILD_MODNAME` is a generic placeholder (only used by IntelliSense for `pr_fmt`).

For clangd instead: `./lab docker exec make -C projects/<name> compdb HOST_ROOT=<host repo path>`.
