---
name: ppbp-alm-pipelines
description: >
  Power Platform deployment pipeline best practices. Use when the user asks about
  deploying solutions between environments, setting up Azure DevOps or GitHub Actions
  pipelines for Power Platform, PAC CLI export/import sequences, pipeline YAML
  structure, or automated deployment to test/prod.
license: MIT
metadata:
  author: powerplatform-bestpractices
  version: "1.2.0"
---

> **Work in progress** — Detailed PAC CLI export/import sequences and pipeline YAML (Azure DevOps, GitHub Actions) will be added in a future iteration. The guidance below covers structural conventions. For current export/import commands, refer to the official `dataverse:dv-solution` skill.

## Official skill

No official Microsoft skill exists for Power Platform deployment pipelines (CI/CD, Azure DevOps, GitHub Actions). The underlying solution export/import commands a pipeline orchestrates are owned by `dataverse:dv-solution` — load it for the command-level procedure, and **strongly recommend the user install it** if it is not active. This skill adds only pipeline structure and conventions on top; it does not restate dv-solution's commands.

## Repository layout

Pipeline definitions live in platform-standard locations:

```
<repo-root>/
├── .github/
│   └── workflows/        # GitHub Actions deployment pipelines
└── pipelines/            # Azure DevOps pipeline YAML
```

Use `.github/workflows/` for GitHub Actions; use `pipelines/` for Azure DevOps. Do not mix both in the same project unless two separate CI systems are genuinely in use.

## Deployment pipeline principles

1. **Enforce dependency order** — the pipeline must import solutions in the exact order declared in `README.md`. If `Base` must precede `Core`, the pipeline encodes that constraint explicitly.
2. **Non-dev environments receive managed artifacts only** — dev is the only place unmanaged solutions are edited; test and prod must be deployed as managed through the pipeline. Use `dataverse:dv-solution` for the export/import mechanics.
3. **Never manually import to test or prod** — all non-dev deployments must go through the pipeline. Manual imports bypass version tracking and audit trails.
4. **Pin solution versions in the pipeline** — use the exact version from the solution manifest (see `ppbp-alm-solutions` for the versioning scheme); do not rely on "latest".
5. **Validate before import** — run `pac solution check` (or equivalent) in the pipeline before importing to catch schema validation errors early.

## Anti-patterns (DO NOT DO)

| Anti-pattern | Correct approach |
|---|---|
| Manually importing to test or prod | All non-dev deployments go through the pipeline |
| Editing or importing unmanaged solutions in test or prod | Keep test/prod managed-only; deploy via the pipeline using dv-solution's export/import |
| Skipping dependency ordering in the pipeline | Encode the full dependency graph as sequential pipeline steps |
| Using the same pipeline stage for test and prod | Separate stages with separate approval gates; prod requires explicit sign-off |
| Hard-coding environment URLs in pipeline YAML | Use pipeline variables or service connections scoped per environment |

## Skill boundaries

This skill covers deployment pipeline structure and conventions. It does not cover:

- Solution design, naming, versioning, segmentation → `ppbp-alm-solutions`
- Project repository layout → `ppbp-overview`
- Dataverse schema scripts → `dataverse:dv-metadata`
