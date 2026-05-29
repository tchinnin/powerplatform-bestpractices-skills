---
name: ppbp-alm
description: >
  Use when the user is discussing Application Lifecycle Management on Power Platform:
  solution design (managed vs. unmanaged), environment strategy (dev/test/prod),
  deployment pipelines (Pipelines for Power Platform, Azure DevOps, GitHub Actions),
  solution segmentation, or publisher/prefix configuration.
license: MIT
metadata:
  author: powerplatform-bestpractices
  version: "1.0"
---

## Best practices

1. **One publisher per project** — define a single publisher with a consistent prefix before creating any solution; changing it later requires renaming all schema objects.
2. **Always export and import as Managed in non-dev environments** — managed solutions protect customisations and enforce clean upgrade paths.
3. **Keep a single unmanaged development solution** per workstream; avoid mixing multiple unmanaged solutions in the same dev environment.
4. **Segment solutions by layer** — separate Data (tables/option sets), Configuration (business rules, workflows), and UI (apps, forms, views) into distinct solutions when teams work in parallel.
5. **Pin all solution dependencies explicitly** — never rely on implicit dependencies; add all referenced components to the solution before export.
6. **Use environment variables for all environment-specific values** (connection references, URLs, config) — never hardcode them in flows or plugins.
7. **Automate pipeline triggers on PR merge**, not on push, to prevent half-baked deployments reaching shared environments.
8. **Version your solution on every export** using semantic versioning; the version is immutable once deployed to production as managed.

## Common pitfalls

**Exporting unmanaged to production** — Unmanaged layers cannot be safely removed and block future upgrades. *Always use managed exports for test and production; only unmanaged stays in dev.*

**Missing connection references in pipeline** — Flows deployed via pipeline fail silently if connection references are not pre-created in the target environment and mapped in the pipeline stage configuration.

**Circular solution dependencies** — Splitting solutions carelessly creates circular references that block import. *Design the dependency graph upfront: Data → Core Logic → UI, with no back-edges.*

**Patching instead of upgrading** — Solution patches (legacy) do not support removing components; they accumulate and inflate the solution. *Use solution upgrades (`Stage for Upgrade` → `Apply Upgrade`) to remove components cleanly.*

**Forgetting to include security roles** — Security roles are solution components; omitting them from the solution means they must be recreated manually in each environment.
