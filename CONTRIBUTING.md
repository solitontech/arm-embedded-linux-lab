# Contributing to ARM Embedded Linux Lab

## Branch Naming
| Type | Pattern | Example |
| :--- | :--- | :--- |
| New project feature | `feature/<project>-<topic>` | `feature/vision-edge-neon-simd` |
| Infrastructure change | `infra/<topic>` | `infra/add-beaglebone-profile` |
| Bug fix | `fix/<topic>` | `fix/deploy-script-ssh-path` |
| Documentation | `docs/<topic>` | `docs/update-adr-bootloader` |

## Commit Messages
We use [Conventional Commits](https://www.conventionalcommits.org/):
```
<type>(<scope>): <short description>

feat(vision-edge): add NEON SIMD pixel threshold kernel
fix(deploy): correct SSH key path resolution in deploy_to_lab.sh
infra(ci): add AArch64 cross-compile smoke test
docs(adr): record decision to use Easymake over CMake
```

## Pull Request Checklist
Before opening a PR, confirm:
- [ ] Code compiles cleanly with the AArch64 cross-compiler
- [ ] No board-specific paths or CPU flags committed to `shared/`
- [ ] New hardware targets have a corresponding `tools/deploy/boards/<name>.env.example`
- [ ] New projects use the `shared/templates/new_project/` scaffold as a starting point
- [ ] CI passes

## Agent Guidance
If you are an AI agent contributing to this repo, read `AGENTS.md` first. Check `.agents/workflows/` for a workflow matching your task before writing any code.
