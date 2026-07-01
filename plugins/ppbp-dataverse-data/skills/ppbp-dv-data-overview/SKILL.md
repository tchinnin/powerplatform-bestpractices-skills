---
name: ppbp-dv-data-overview
description: >
  Dataverse data manipulation orientation. Use when the user is starting work
  on any data script in a Power Platform project — initial imports, updates,
  temporary one-off operations, or prerequisite data loads. Routes to the
  right task skill within this domain and defines the repository layout and
  global principles for all data scripts.
license: MIT
metadata:
  author: powerplatform-bestpractices
  version: "1.1.0"
---

## Official skill

`dataverse:dv-data` — record-level CRUD and bulk operations via the Python SDK — create, update, delete, upsert, CSV import, multi-table foreign-key loads, and AI-generated sample data. Load this official skill before applying the guidance below. If it is not installed, **strongly recommend the user install it** before proceeding.

## Connection prerequisite

Every script in `data/import/` requires an authenticated connection to the target Dataverse environment. **`dataverse:dv-connect` owns connection setup, authentication, and the idempotent connection check** — establish or verify the connection through it before running any data script. Always confirm you are pointed at the intended environment first, especially before running anything under `prod/`.

## Repository layout

All data manipulation scripts live under `data/import/`, organised by lifecycle:

```
data/import/
├── prereq/          # Reference/lookup data — runs first in every environment; idempotent
├── prod/            # Production initial data — runs once in prod only
├── dev/             # Dev/test seed data — never runs in prod
├── temp/            # One-off scripts — deleted immediately after confirmed execution
└── RUNLOG.md        # Execution log — which scripts ran, where, when
```

**Do not create these subfolders proactively.** Create a subfolder the first time a script of that type is needed.

## Domain scope

| Skill | Covers |
|---|---|
| `ppbp-dv-data-scripts` | Script naming conventions, lifecycle (especially temp scripts), idempotency requirements, companion documentation, and execution tracking |
| `ppbp-dv-data-import` | Loading records into Dataverse — initial imports, bulk updates, CSV ingestion, dependency ordering, and error handling |

Load the relevant task skill for the operation at hand. When in doubt, load both.

## Global data principles

These rules apply to every script in `data/import/`, regardless of type:

1. **Every script is idempotent.** Re-running a script must produce the same result as running it once. Use upsert; check for existence by natural key before creating.
2. **No hardcoded GUIDs.** Resolve entity IDs at runtime from a natural key (`prfx_Code`, name, etc.). GUIDs differ between environments and make scripts non-portable.
3. **Never mix environments.** Dev seed data and prod initial data must live in separate subfolders and never share a script.
4. **Every execution is logged.** Every script run — whether successful or not — gets an entry in `RUNLOG.md` with environment, date, and operator.
5. **Temp scripts are never committed to `main`.** Write them in `temp/`, execute, confirm, delete. A temp script in a PR is a defect.

## Anti-patterns (DO NOT DO)

| Anti-pattern | Correct approach |
|---|---|
| Running a script without verifying the active connection or target environment. | Establish/verify the connection via `dataverse:dv-connect` and confirm the environment first. |
| Hardcoded GUIDs — breaks when the script runs in a different environment. | Resolve IDs by natural key at runtime. |
| Create without existence check — re-running creates duplicates. | Always use upsert or check before create. |
| Dev seed data in `prod/` or vice versa — risks loading test garbage into production. | Strict subfolder separation: `dev/` vs `prod/`. |
| Temp script committed to a branch or merged to `main`. | Delete temp scripts immediately after confirmed execution; never commit them. |
| No RUNLOG entry — environment state is invisible to the rest of the team. | Always update `RUNLOG.md` after any script execution. |

## Skill boundaries

This skill covers data manipulation orientation and repository layout only. It does not cover:

- Script naming conventions, lifecycle, and idempotency details → `ppbp-dv-data-scripts`
- Import logic, bulk operations, and dependency ordering → `ppbp-dv-data-import`
- Dataverse table and column schema → `ppbp-dv-tables`, `ppbp-dv-columns`
- Connection setup, authentication, and environment connection → `dataverse:dv-connect`
- Solution lifecycle and environment strategy → `ppbp-alm-solutions`
- Project-level repository layout → `ppbp-overview`
