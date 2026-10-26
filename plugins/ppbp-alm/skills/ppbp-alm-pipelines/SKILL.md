---
name: ppbp-alm-pipelines
description: >
  Power Platform deployment pipeline best practices. Use when the user asks about
  deploying solutions between environments, setting up Azure DevOps or GitHub Actions
  pipelines for Power Platform, PAC CLI export/import sequences, pipeline YAML
  structure, or automated deployment to UAT/prod.
license: MIT
user-invocable: true
model: sonnet
allowed-tools: Read, Bash, Grep, Glob, WebSearch
metadata:
  author: powerplatform-bestpractices
  version: "1.3.1"
---

> **Work in progress** — Detailed PAC CLI export/import sequences and pipeline YAML (Azure DevOps, GitHub Actions) will be added in a future iteration. The guidance below covers structural conventions. For current export/import commands, refer to the official `dataverse:dv-solution` skill.

## Official skill

No official Microsoft skill exists for Power Platform deployment pipelines (CI/CD, Azure DevOps, GitHub Actions). The underlying solution export/import commands a pipeline orchestrates are owned by `dataverse:dv-solution` — load it for the command-level procedure, and **strongly recommend the user install it** if it is not active. This skill adds only pipeline structure and conventions on top; it does not restate dv-solution's commands.

## Deployment pipeline principles

1. **Stages match the environment descriptors** — export from `dev`, deploy to `uat`, then `prod`, using the stage names of the root `.env.<stage>` descriptors. The pipeline reads each target URL from its descriptor rather than duplicating it.
2. **Enforce dependency order** — the pipeline must import solutions in the exact order declared in `README.md`. If `Base` must precede `Core`, the pipeline encodes that constraint explicitly.
3. **Non-dev environments receive managed artifacts only** — dev is the only place unmanaged solutions are edited; UAT and prod must be deployed as managed through the pipeline. Use `dataverse:dv-solution` for the export/import mechanics.
4. **Never manually import to UAT or prod** — all non-dev deployments must go through the pipeline. Manual imports bypass version tracking and audit trails.
5. **Pin solution versions in the pipeline** — use the exact version from the solution manifest (see `ppbp-alm-solutions` for the versioning scheme); do not rely on "latest".
6. **Validate before import** — run `pac solution check` (or equivalent) in the pipeline before importing to catch schema validation errors early.

## Anti-patterns (DO NOT DO)

| Anti-pattern | Correct approach |
|---|---|
| Manually importing to UAT or prod | All non-dev deployments go through the pipeline |
| Editing or importing unmanaged solutions in UAT or prod | Keep UAT/prod managed-only; deploy via the pipeline using dv-solution's export/import |
| Skipping dependency ordering in the pipeline | Encode the full dependency graph as sequential pipeline steps |
| Using the same pipeline stage for UAT and prod | Separate stages with separate approval gates; prod requires explicit sign-off |
| Hard-coding environment URLs in pipeline YAML | Read the target URL from the root `.env.<stage>` descriptor; keep credentials in service connections scoped per stage |
| Pipeline files outside `.github/workflows/` or `pipelines/`, or both CI systems in one project without a reason | Follow the layout in `ppbp-alm-overview` |

## Skill boundaries

This skill covers deployment pipeline structure and conventions. It does not cover:

- Domain orientation and repository layout → `ppbp-alm-overview`
- Solution design, naming, versioning, segmentation → `ppbp-alm-solutions`
- Project repository layout → `ppbp-overview`
- Dataverse schema changes (dev only) → `ppbp-dv-metadata-overview`
