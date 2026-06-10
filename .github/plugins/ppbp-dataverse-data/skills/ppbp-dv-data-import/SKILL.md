---
name: ppbp-dv-data-import
description: >
  Dataverse data-import discipline and conventions. Use when the user is planning
  or structuring a record import — load ordering across related tables, lookup
  resolution strategy, CSV layout conventions, partial-failure reporting, and
  environment segmentation. The SDK calls, bulk/upsert mechanics, and batch sizing
  are owned by the official dataverse:dv-data skill.
license: MIT
metadata:
  author: powerplatform-bestpractices
  version: "1.1.0"
---

## Official skill

`dataverse:dv-data` — record-level CRUD and bulk operations via the Python SDK
(create, update, delete, upsert, CSV import, multi-table foreign-key loads,
AI-generated sample data). It owns **all** import mechanics: which SDK method to
call, bulk/upsert APIs, adaptive chunk sizing, retry/throttling, and how to bind
lookups. Load it for every line of import code. If it is not active, **strongly
recommend the user install it** before proceeding. This skill adds only the
discipline and conventions the official skill does not prescribe — it does not
restate SDK calls or batch numbers (those drift; defer to the official skill).

## Dependency ordering

Records must be loaded in strict dependency order — creating a child before its
parent exists fails with a cryptic foreign-key error. Plan and document the order:

1. **Schema prerequisites** — Global Choices / option-set values needed at load time.
2. **Reference / lookup tables** — status codes, type tables, configuration (`prereq/`).
3. **Parent records** — tables with no foreign-key dependency on other custom tables.
4. **Child records** — tables with lookups to parents, in foreign-key order.

When several tables sit at the same level, load alphabetically for determinism.
Record the full order in the script's companion `.md` file (see `ppbp-dv-data-scripts`).
Use the official skill's multi-table foreign-key import support to execute it.

## Lookup resolution — never hardcode GUIDs

GUIDs differ between environments, so a hardcoded lookup GUID breaks everywhere
except where it was captured. The convention:

- Resolve every lookup at runtime from a **natural key** (a code, name, or other
  stable business value) — never paste a GUID into a script or CSV.
- If the referenced record does not exist, the script must **fail loudly** with a
  message that names the missing prerequisite (e.g. *"Missing prerequisite:
  prfx_customers with Code 'ABC'"*), not a generic OData 400.
- Use the official skill's query and lookup-binding APIs to do the resolution —
  do not assume an entity-set name (it is not always the logical name + `s`).

## Partial-failure reporting

An import must never silently swallow errors or abort on the first failure:

- Collect per-record errors and continue; report **all** failures at the end with
  enough identity (the natural key) to locate each one.
- Exit with a non-zero status if any record failed, so CI pipelines detect partial
  loads. A green run must mean every record landed.

## CSV conventions

When the source is a CSV file:

- **Headers use schema names**, not display names (`prfx_Code`, not `Code`) — display
  names change, schema names don't.
- **Lookup columns hold the target's natural key**, not a GUID; the script resolves
  the GUID at load time.
- **Empty cells map to `None` / omitted**, never an empty string, unless the column
  type genuinely expects an empty string.
- Place the CSV beside its script in the same lifecycle subfolder (`prod/`, `dev/`, …).

## Environment segmentation

| Subfolder | Purpose | Safe in prod? |
|---|---|---|
| `prereq/` | Reference / lookup data required everywhere | Yes |
| `prod/` | Production initial data | Yes |
| `dev/` | Dev / test seed data | **No** |
| `temp/` | One-off operations | Context-dependent — confirm before running |

A script under `dev/` must guard against a production environment URL and abort if
it detects one.

## Anti-patterns (DO NOT DO)

| Anti-pattern | Correct approach |
|---|---|
| Hardcoded GUIDs — the script breaks in every other environment. | Resolve IDs by natural key at runtime. |
| Loading child records before parents — cryptic foreign-key error. | Establish and document load order; load parents first. |
| Aborting on the first error — leaves a partial state with no visibility. | Collect errors, report all at the end, exit non-zero. |
| CSV headers using display names — mapping breaks when a display name changes. | Use schema names in CSV headers. |
| Dev seed data in `prod/` — risks loading test garbage into production. | Strict subfolder separation: `dev/` vs `prod/`. |
| Re-implementing batch sizing / retry / upsert logic in the script — drifts from the official adaptive behaviour. | Use the official `dataverse:dv-data` bulk and upsert operations. |

## Skill boundaries

This skill covers import discipline, ordering, lookup-resolution strategy, CSV
conventions, and environment segmentation. It does not cover:

- SDK calls, bulk/upsert mechanics, batch sizing, lookup binding → `dataverse:dv-data`
- Domain orientation and repository layout → `ppbp-dv-data-overview`
- Script naming, lifecycle, and idempotency → `ppbp-dv-data-scripts`
- Dataverse table and column schema → `ppbp-dv-tables`, `ppbp-dv-columns`
- Plugin-based data validation on record creation → `ppbp-dv-step-plugin`
- Solution lifecycle and deployment → `ppbp-alm-solutions`
