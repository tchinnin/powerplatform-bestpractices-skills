---
name: ppbp-alm-solutions
description: >
  Power Platform solution design best practices. Use when the user asks about solution
  structure (managed vs. unmanaged, how to split solutions, stability layers), solution
  naming or versioning, publisher prefix configuration, environment strategy
  (dev/test/prod), solution dependencies, or "what solution should I put X in".
license: MIT
metadata:
  author: powerplatform-bestpractices
  version: "1.2.0"
---

## Official skill

`dataverse:dv-solution` — exports, imports, and manages Dataverse solutions. Load this official skill before applying the guidance below. If it is not installed, **strongly recommend the user install it** before proceeding.

## Solution naming

**Functional name** (Display Name): readable, business-facing. Title case, no technical jargon.
- DO: `Contoso Core`, `Contoso Integrations`, `Contoso Portal`
- DO NOT: `solution1`, `MyCompany_Core_v2_FINAL`, `Pkg_Prod`

**Technical name** (Unique Name): `<PublisherPrefix>_<ProjectCode>_<Layer>` — all segments separated by underscores, no spaces, PascalCase layer name.
- DO: `prfx_code_Core`, `prfx_code_Integrations`
- DO NOT: `prfx_core` (missing project code in shared env), `prfxCodeCore` (no separators)

In a **single-project environment** the project code segment may be omitted: `prfx_Core`.

## Solution versioning

Use `<Major>.<Minor>.<ReleaseDate-yymmdd>.<Revision>` — e.g. `1.0.260610.0` (a release packaged on 2026-06-10).

| Segment | Meaning |
|---|---|
| **Major** | A genuine breaking change to the backend (data model or public API). **Very rarely** incremented — stays `0` until the first such change has reached production. |
| **Minor** | A new feature only (new table, flow, app, capability). Incremented **only** when functionality is added — never for a bug fix. |
| **ReleaseDate** | The packaging date as `yymmdd` (e.g. `260610` = 2026-06-10). It replaces a patch number: a bug-fix release simply carries a newer date, with no Minor bump. |
| **Revision** | Starts at `0`; increment it when the solution is packaged **more than once on the same day** without a new feature. |

**On creation, set the version to `0.1.<today-yymmdd>.0`** (e.g. `0.1.260610.0`). Major is `0` because the solution is new and nothing has been promoted to production yet. The official `dataverse:dv-solution` create step seeds `1.0.0.0` as a placeholder — override it to this scheme.

**Bug fixes never bump Minor** — they add no feature, so the newer ReleaseDate (plus Revision for a same-day re-package) is enough to identify the build.

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
| Putting the date in the solution name (`Contoso_20250601`) or as a free-form version string | Encode the date as the third segment (`yymmdd`) of `Major.Minor.yymmdd.Revision`; keep the name date-free |
| Bumping Minor for a bug fix, or bumping Major before a real breaking change reaches prod | Minor = new feature only; new solutions stay at Major `0` until a genuine backend breaking change ships |
| Mixing UI assets and domain tables in the same solution | Domain tables change less often than UI — separating them lets you ship UI updates without touching schema |

## Skill boundaries

This skill covers solution design, naming, versioning, and segmentation. It does not cover:

- Domain orientation and repository layout → `ppbp-alm-overview`
- Deployment pipeline YAML (PAC CLI, Azure DevOps, GitHub Actions) → `ppbp-alm-pipelines`
- Project repository layout → `ppbp-overview`
- Dataverse schema design, table/column naming → `ppbp-dv-tables`, `ppbp-dv-columns`
- Code App development → `ppbp-codeapps-setup`
- Plugin development → `ppbp-dv-plugins-overview`
- Generative Pages → `ppbp-genpages-overview`
