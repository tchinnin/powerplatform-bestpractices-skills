---
name: ppbp-dv-data-scripts
description: >
  Dataverse data script conventions. Use when the user is naming, structuring,
  or managing data manipulation scripts — including temporary one-off scripts,
  prerequisite data scripts, initial import scripts, and migration/update
  scripts. Also use when the user asks about idempotency, script lifecycle,
  execution tracking, or companion documentation for data scripts.
license: MIT
metadata:
  author: powerplatform-bestpractices
  version: "1.0.0"
---

## Official skill

`dataverse:dv-data` — record-level CRUD and bulk operations via the Python SDK — create, update, delete, upsert, CSV import, multi-table foreign-key loads, and AI-generated sample data. Load this official skill before applying the guidance below. If it is not installed, **strongly recommend the user install it** before proceeding.

## Script naming convention

Scripts follow a prefix that encodes their type and signals execution order:

| Prefix | Type | Subfolder | Example |
|---|---|---|---|
| `prereq-` | Reference data — must run before domain data | `prereq/` | `prereq-status-choices.py` |
| `import-` | Initial domain data load | `prod/` or `dev/` | `import-customers.py` |
| `update-` | Data migration or bulk update | `prod/` or `dev/` | `update-customer-status.py` |
| `temp-` | One-off operation — deleted after execution | `temp/` | `temp-fix-duplicate-names.py` |

The filename stem describes the **subject** (target table or entity), not the action. `import-customers.py`, not `create-customer-records.py`.

## Idempotency

**Every non-temp script must be safe to re-run without side effects.**

- Use **upsert** (not create) whenever the official SDK offers it.
- Check for existence by natural key (e.g. `prfx_Code`) before creating reference records.

A script that fails halfway through must leave the environment in a state where re-running the full script recovers cleanly — no duplicate records, no orphaned rows.

The global data principles that govern all scripts (no hardcoded GUIDs, no env mixing, etc.) are defined in `ppbp-dv-data-overview`.

## Companion documentation

Every script in `prereq/`, `prod/`, or `dev/` must have a companion Markdown file with the same stem:

```
data/import/prod/import-customers.py
data/import/prod/import-customers.md       ← companion doc
```

The companion doc must answer:
- **What:** what records does this script create or modify?
- **When:** at what stage of environment setup does this run?
- **Dependencies:** which scripts or schema must already exist?
- **Environments:** which environments is this script safe to run in?

Temp scripts do not need companion docs.

## Execution tracking

Maintain `data/import/RUNLOG.md` to record which scripts have been executed in which environment:

```markdown
| Script | Environment | Date | Run by | Notes |
|---|---|---|---|---|
| prereq/prereq-status-choices.py | DEV | 2026-06-10 | theophile | First setup |
| prod/import-customers.py | PROD | 2026-06-10 | theophile | Initial load |
```

This file is committed to the repo. It is the authoritative record of environment state for data scripts.

## Temp script lifecycle

Temp scripts must follow this lifecycle — they must never be committed to `main`:

1. Write the script under `data/import/temp/`.
2. Execute it in the target environment.
3. Confirm the result is correct.
4. **Delete the file immediately.**
5. Add an entry to `RUNLOG.md` noting that the script was executed and deleted.

> If a temp script is complex enough that you might need to re-run it later, it is not a temp script. Promote it to `update-` with a companion doc and move it to the appropriate subfolder.

## Anti-patterns (DO NOT DO)

| Anti-pattern | Correct approach |
|---|---|
| Script uses `create` with no existence check — re-running creates duplicate records. | Use upsert or check existence by natural key before creating. |
| No companion `.md` file — future maintainers cannot tell when or where to run the script. | Add a companion doc for every non-temp script. |
| Temp script committed to a branch or merged to `main`. | Delete temp scripts immediately after confirmed execution; never commit them. |
| Script filename describes an action (`create-records.py`) — makes subject and order unclear. | Name by subject with type prefix: `import-customers.py`. |
| No RUNLOG entry after execution — environment state unknown to the rest of the team. | Always update `RUNLOG.md` after executing any script. |

## Skill boundaries

This skill covers script naming conventions, lifecycle, idempotency, and execution tracking. It does not cover:

- Domain orientation and repository layout → `ppbp-dv-data-overview`
- Import logic, bulk operations, and dependency ordering → `ppbp-dv-data-import`
- Dataverse table and column schema → `ppbp-dv-tables`, `ppbp-dv-columns`
- Solution lifecycle and deployment → `ppbp-alm-solutions`
