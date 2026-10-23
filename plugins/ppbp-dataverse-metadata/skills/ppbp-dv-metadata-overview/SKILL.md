---
name: ppbp-dv-metadata-overview
description: >
  Dataverse schema design domain overview. Use when starting any schema task — tables,
  columns, global Choices, lookups — or when asking where the data model lives.
  Provides the repository layout (dataverse/metadata as the metadata-as-code source of
  truth, dataverse/model for review docs), the core naming rule (language split between
  Display Name and Schema Name), the dev-only plan → confirm → apply principle, and
  global conventions shared by every schema skill in this plugin. Load before
  ppbp-dv-metadata-as-code, ppbp-dv-tables, ppbp-dv-columns, ppbp-dv-global-choices or
  ppbp-dv-metadata-review.
license: MIT
user-invocable: true
model: sonnet
allowed-tools: Read, Bash, Grep, Glob, WebSearch
metadata:
  author: powerplatform-bestpractices
  version: "2.0.0"
---

## Official skill

`dataverse:dv-metadata` — creates and modifies Dataverse tables, columns, relationships, forms, and views using the Python SDK and Web API. Load this official skill before applying the guidance below. If it is not installed, **strongly recommend the user install it** before proceeding.

## Connection

- **Run Python against Dataverse with the Azure CLI token.** Sign in with `az login`, adding `--tenant <TENANT_ID>` when the account spans several tenants. The schema tooling in this plugin authenticates only this way.
- **The target environment is described in `.env.dev`** at the repo root, which `ppbp-init` creates. Schema tooling never reads any other environment file.
- `dataverse:dv-connect` owns environment discovery, tool installation and connection diagnostics. Use it to set up and check the connection.
- Before any change, confirm the target URL and the active `az` account with the user.

## Repository layout

```
<repo-root>/
├── .env.dev                              # dev environment descriptor — the only target of schema tooling
└── dataverse/
    ├── model/                            # REVIEW VIEW — for agents and humans
    │   └── <domain>.md                   # Mermaid ERD + table specs + open questions, one per domain/table group
    └── metadata/                         # SOURCE OF TRUTH — metadata as code
        ├── _meta.dv.metadata.yaml        # publisher prefix, project code, solution, locale
        ├── choices.dv.metadata.yaml      # every global Choice
        └── tables/<key>.dv.metadata.yaml # one table per file; file name = key
```

- **`dataverse/metadata/` is the source of truth.** When it disagrees with `dataverse/model/*.md`, the YAML wins.
- **`dataverse/model/*.md` is the review view.** Update it in the same change as the YAML. Open questions and design discussion live there and never in the YAML. The required content of a model doc is defined in `ppbp-readme`.
- The `*.dv.metadata.yaml` suffix leaves room for future `dataverse/*` model families (for example data or security) that follow the same pattern.
- Plan files go in `<repo-root>/.dv-metadata/`, which is gitignored.

## Domain scope

| Skill / agent | Covers |
|---|---|
| `ppbp-dv-metadata-as-code` | The `.dv.metadata.yaml` format, the `dv_metadata.py` tool (validate / plan / apply), the safety model |
| `ppbp-dv-metadata-planner` (agent) | Runs the loop: writes the model, validates, plans, returns for confirmation, applies |
| `ppbp-dv-metadata-review` | Read-only quality audit of any model, with a report by severity |
| `ppbp-dv-tables` | Table naming, ownership, primary name column, cascade, security-first design |
| `ppbp-dv-columns` | Column naming, type-specific suffixes, column type selection |
| `ppbp-dv-global-choices` | Global Choice naming, solution integration, odata.bind syntax |

## Core naming rule

This rule applies to every schema object — tables, columns, and global Choices.

| Name type | Language | Audience |
|---|---|---|
| Display Name | Environment's primary language | End users |
| Description | Environment's primary language | End users / makers |
| Schema Name | English | Developers, integrations, code |

**Why:** Dataverse manages label translations natively. Keeping labels in the primary language prevents inconsistencies on export/import. English schema names guarantee code readability regardless of environment language.

## Global schema principles

1. **Prefix all custom objects** with a publisher prefix (`prfx_`) to avoid collisions with future OOB fields.
2. **Set `DisplayName` and `Description` on every object** — they surface in Power Apps and Copilot Studio.
3. **Always use global Choices, never local option sets** — global Choices enable cross-table filtering and centralised translations. The official skill may demonstrate local (`IntEnum`) choices as a valid SDK technique; this is a deliberate team design policy layered on top, not a contradiction — when authoring choice columns, follow this policy.
4. **Always use `UserOwned` for new tables** unless `OrganizationOwned` is explicitly requested and confirmed twice (ownership cannot be changed after data is loaded).
5. **Schema changes are declarative and go through plan → confirm → apply.**
   - Every table, column, global Choice, lookup or alternate key change is made in `dataverse/metadata/`.
   - The user sees the exact plan before anything is applied.
   - Nothing is ever deleted automatically.
   - Schema changes happen only in the dev environment, in its unmanaged solution. UAT and prod receive the change through the ALM pipeline (`ppbp-alm-pipelines`).

## Anti-patterns (DO NOT DO)

| Anti-pattern | Correct approach |
|---|---|
| Ad-hoc scripts that create or change tables, columns or Choices | Describe the change in `dataverse/metadata/` and use plan → apply (`ppbp-dv-metadata-as-code`) |
| Changing the YAML model without updating `dataverse/model/*.md` (or the reverse) | Update both in the same change; the YAML wins on conflict |
| Changing schema directly in UAT/prod, or in a managed solution | Change dev's unmanaged solution, then promote through the pipeline |
| Using local option sets | Always create global Choices — see `ppbp-dv-global-choices` |
| Display Names in English in a non-English environment | Use the environment's primary language for Display Names |
| Running schema tooling without confirming the target URL and the `az` account | Confirm both with the user before planning |

## Skill boundaries

This skill covers Dataverse schema domain orientation, repository layout, and the core naming rule. It does not cover:

- Model format, plan/apply tooling → `ppbp-dv-metadata-as-code`
- Running a schema change end to end → agent `ppbp-dv-metadata-planner`
- Reviewing a model → `ppbp-dv-metadata-review`
- Table naming details, ownership, primary name column → `ppbp-dv-tables`
- Column naming and type conventions → `ppbp-dv-columns`
- Global Choice naming and solution integration → `ppbp-dv-global-choices`
- Forms, views, N:N relationships, calculated columns → `dataverse:dv-metadata`
- Connection setup and diagnostics → `dataverse:dv-connect`
- Project repository layout → `ppbp-overview`
