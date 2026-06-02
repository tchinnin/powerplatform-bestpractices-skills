---
name: ppbp-alm
description: >
  Power Platform ALM best practices. Use when the user asks about solution design
  (managed vs. unmanaged, how to split solutions, stability layers), solution naming
  or versioning, publisher prefix configuration, environment strategy (dev/test/prod),
  solution dependencies, or deployment pipelines (Azure DevOps, GitHub Actions,
  Pipelines for Power Platform). Also use when the user asks "what solution should
  I put X in" or "how do I deploy to test/prod".
license: MIT
metadata:
  author: powerplatform-bestpractices
  version: "0.1.0"
---

> **Work in progress** — Deployment pipeline guidance (PAC CLI sequences, Azure DevOps / GitHub Actions YAML) will be added in a future iteration. Solution design conventions below are stable.

## Official skill

`dataverse:dv-solution` — exports, imports, and manages Dataverse solutions. Load this official skill before applying the guidance below. If it is not installed, **strongly recommend the user install it** before proceeding.

## Repository layout

ALM assets do not have a dedicated top-level folder — they live in platform-standard locations (see `ppbp-overview` for the full canonical tree):

```
<repo-root>/
├── .github/
│   └── workflows/        # GitHub Actions deployment pipelines
└── pipelines/            # Azure DevOps pipeline YAML (alternative to .github/workflows/)
```

Power Platform solutions are managed in the platform itself, not stored in the repository as unpacked XML unless the project explicitly exports them. If solution XML is committed, store it under `solutions/<solution-unique-name>/`.

## Solution naming

**Functional name** (Display Name): readable, business-facing. Title case, no technical jargon.
- DO: `Contoso Core`, `Contoso Integrations`, `Contoso Portal`
- DO NOT: `solution1`, `MyCompany_Core_v2_FINAL`, `Pkg_Prod`

**Technical name** (Unique Name): `<PublisherPrefix>_<ProjectCode>_<Layer>` — all segments separated by underscores, no spaces, PascalCase layer name.
- DO: `prfx_code_Core`, `prfx_code_Integrations`
- DO NOT: `prfx_core` (missing project code in shared env), `prfxCodeCore` (no separators)

In a **single-project environment** the project code segment may be omitted: `prfx_Core`.

## Solution versioning

Use `Major.Minor.Patch.Build` (e.g. `1.2.0.0`).

| Increment | When |
|---|---|
| **Major** | Breaking change — table removed, column type changed, public API changed |
| **Minor** | New feature — new table, new flow, new app added |
| **Patch** | Bug fix or non-breaking config change |
| **Build** | CI/CD pipeline counter (auto-incremented, never set manually) |

Never ship managed solutions with `0.x` versions to production. Reach `1.0.0.0` before the first prod deployment.

## Solution segmentation

Split solutions along **stability and release cadence**, not by asset type.

| Layer | What belongs here | What does NOT belong |
|---|---|---|
| **Base / Shared** | Publisher, global Choices, shared reference tables, security roles | App-specific tables, flows that depend on app logic |
| **Core domain** | Domain tables, relationships, business rules (plugins, Custom APIs) | UI apps, integration flows |
| **App layer** | Canvas/model-driven apps, site maps, forms, views | Tables that other solutions depend on |
| **Integration layer** | Flows, connectors, external-facing Custom APIs | UI assets, core domain tables |

Rules:
- A solution must be **importable independently** after its dependencies are present.
- **Never** put a component that another solution depends on in a higher-layer solution.
- Keep the **Base / Shared** solution as thin as possible — everything in it blocks all other solutions.

## Dependency ordering

Document the dependency chain in the project `README.md` (see `ppbp-overview`). The import order at deploy time must exactly match the declared dependency graph — enforce this in your pipeline.

## Anti-patterns (DO NOT DO)

| Anti-pattern | Correct approach |
|---|---|
| One solution for the entire project | Split by stability layer — Base → Core → App/Integration; reduces blast radius of changes |
| Importing solutions out of dependency order | Declare the full dependency graph in README and enforce order in the pipeline |
| Versioning with a date suffix (`_20250601`) | Use semantic `Major.Minor.Patch.Build`; dates as versions break upgrade detection |
| Setting version to `1.0.0.0` before prod is ready | Keep `0.x` during active development; go to `1.0.0.0` only on first prod release |
| Mixing UI assets and domain tables in the same solution | Domain tables change less often than UI — separating them lets you ship UI updates without touching schema |

## Deployment pipelines

> **Work in progress** — PAC CLI export/import sequences and pipeline YAML (Azure DevOps, GitHub Actions) will be documented here. In the meantime, refer to the official `dataverse:dv-solution` skill for current export/import commands.

## Skill boundaries

This skill covers solution design, naming, versioning, and deployment pipeline patterns. It does not cover:

- Project repository layout and skill routing → `ppbp-overview`
- Dataverse schema design, table/column naming → `ppbp-dv-metadata`
- Code App development → `ppbp-code-apps`
- Plugin development → `ppbp-dv-plugins`
- Generative Pages → `ppbp-generative-pages`
