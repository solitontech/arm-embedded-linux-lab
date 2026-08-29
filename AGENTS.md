# ARM Embedded Linux Lab — Agent Principles

This is a professional embedded Linux monorepo supporting multiple projects and hardware targets.

**Design for reuse:** Any code, script, or configuration that could serve more than one project belongs in `shared/`. Projects should consume shared resources, not duplicate them.

**Design for scale:** Never couple a script, tool, or library to a specific project or hardware board. Use variables and profiles so the same infrastructure can target any controller.

**Separate concerns cleanly:** Each top-level directory has a single purpose — respect those boundaries. Don't put infrastructure in project space. Don't put application logic in shared space.

## How to Operate in This Repo

Before starting any task, check `.agents/workflows/` for a workflow matching your task. If one exists, follow it. If not, complete your task and create a new workflow using `.agents/workflows/WORKFLOW_TEMPLATE.md` so future agents can benefit.

For reusable atomic operations (e.g., cross-compiling, deploying to a board), check `.agents/skills/` first. Create new skills using `.agents/skills/SKILL_TEMPLATE.md`.
