---
name: ppbp-alm-overview
description: >
  Power Platform ALM domain overview. Use when starting any ALM-related task —
  solution design, deployment, or environment strategy. Provides the canonical
  repository layout for ALM assets and global conventions shared across all ALM
  skills in this plugin. Load before ppbp-alm-solutions or ppbp-alm-pipelines.
license: MIT
metadata:
  author: powerplatform-bestpractices
  version: "1.1.0"
---

## Official skill

`dataverse:dv-solution` — exports, imports, and manages Dataverse solutions. Load this official skill before applying the guidance below. If it is not installed, **strongly recommend the user install it** before proceeding. Note that dv-solution covers only the **solution-lifecycle** slice of this domain; deployment pipelines and environment strategy have **no official Microsoft skill** — that guidance here is additive and stands on its own.

## Repository layout

ALM assets live in platform-standard locations:

```
<repo-root>/
├── .github/
│   └── workflows/        # GitHub Actions deployment pipelines
├── pipelines/            # Azure DevOps pipeline YAML
└── solutions/
    └── <solution-unique-name>/   # Unpacked solution XML (only if the project exports solutions to source control)
```

- Use `.github/workflows/` for GitHub Actions and `pipelines/` for Azure DevOps. Do not mix both unless two CI systems are genuinely in use.
- Solutions are managed in the Power Platform itself. Commit unpacked XML to `solutions/` only when the project explicitly version-controls solution source.

## Domain scope

This plugin covers the full Power Platform ALM lifecycle:

| Skill | Covers |
|---|---|
| `ppbp-alm-solutions` | Solution design, naming, versioning, segmentation layers, dependency ordering |
| `ppbp-alm-pipelines` | Deployment pipeline structure, managed vs. unmanaged, CI/CD conventions |

## Global ALM principles

1. **Environments are promotion stages, not workspaces** — only Dev is used for active development; Test and Prod receive managed imports via pipeline, never manual changes.
2. **Solutions encode the dependency graph** — the import order at deploy time must match the declared dependency graph in `README.md`.
3. **Versioning is the contract** — solution version numbers communicate breaking vs. additive changes; treat them as a public API.

## Anti-patterns (DO NOT DO)

| Anti-pattern | Correct approach |
|---|---|
| Manual imports to Test or Prod | All non-dev deployments go through the pipeline |
| Storing unpacked solution XML at repo root | Use `solutions/<unique-name>/` if you export to source control |

## Skill boundaries

This skill covers ALM domain orientation and repository layout. It does not cover:

- Solution design, naming, versioning → `ppbp-alm-solutions`
- Deployment pipeline YAML and CI/CD → `ppbp-alm-pipelines`
- Project repository layout → `ppbp-overview`
