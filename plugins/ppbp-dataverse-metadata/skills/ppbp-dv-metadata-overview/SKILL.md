---
name: ppbp-dv-metadata-overview
description: >
  Dataverse schema design domain overview. Use when starting any schema task — tables,
  columns, global Choices, lookups — or when asking where the data model lives.
  Provides the repository layout (dataverse/model for review docs), the core naming rule
  (language split between Display Name and Schema Name), the dev-only, confirm-first
  change principles, and global conventions shared by every schema skill in this
  plugin, whatever tool applies the changes. Load before ppbp-dv-tables,
  ppbp-dv-columns, ppbp-dv-global-choices or ppbp-dv-metadata-review.
license: MIT
user-invocable: true
model: sonnet
allowed-tools: Read, Bash, Grep, Glob, WebSearch
metadata:
  author: powerplatform-bestpractices
  version: "3.0.0"
---

## Official skill

`dataverse:dv-metadata` — creates and modifies Dataverse tables, columns, relationships, forms, and views using the Python SDK and Web API. Load this official skill before applying the guidance below. If it is not installed, **strongly recommend the user install it** before proceeding.

## Connection

- **Run Python against Dataverse with the Azure CLI token.** Sign in with `az login`, adding `--tenant <TENANT_ID>` when the account spans several tenants.
- **The dev environment is described in `.env.dev`** at the repo root, which `ppbp-init` creates. Whatever tool changes the schema, it targets that environment and nothing else.
- `dataverse:dv-connect` owns environment discovery, tool installation and connection diagnostics. Use it to set up and check the connection.
- Before any change, confirm the target URL and the active `az` account with the user.

## Repository layout

```
<repo-root>/
├── .env.dev                              # dev environment descriptor — the only target of schema changes
└── dataverse/
    └── model/                            # REVIEW VIEW — for agents and humans
        └── <domain>.md                   # Mermaid ERD + table specs + open questions, one per domain/table group
```

- **`dataverse/model/*.md` is the review view of the schema.** Update it in the same change as the schema itself. Open questions and design discussion live there. The required content of a model doc is defined in `ppbp-readme`.
- **If the project defines its schema as code**, the tool's source files live under `dataverse/`, in that tool's own format and paths. They never replace the review doc.

## Domain scope

| Skill / agent | Covers |
|---|---|
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
5. **Schema changes follow the same rules, whatever tool applies them.**
   - They happen only in the dev environment, in its unmanaged solution. UAT and prod receive the change through the ALM pipeline (`ppbp-alm-pipelines`).
   - The user sees and confirms the exact change before it is applied.
   - Nothing is ever deleted automatically. A delete needs an explicit double confirmation.
   - Prefer a reproducible, version-controlled definition of the change over one-off clicks or ad-hoc scripts. One implementation of this: the `dataverse-as-code` marketplace (`dvac-metadata`).

## Anti-patterns (DO NOT DO)

| Anti-pattern | Correct approach |
|---|---|
| One-off scripts or unrecorded clicks that create or change tables, columns or Choices | Keep a reproducible, versioned definition of the change, and show it to the user before applying |
| Changing the schema without updating `dataverse/model/*.md` | Update the review doc in the same change |
| Applying a schema change the user hasn't confirmed | Show the exact change first, then apply |
| Changing schema directly in UAT/prod, or in a managed solution | Change dev's unmanaged solution, then promote through the pipeline |
| Using local option sets | Always create global Choices — see `ppbp-dv-global-choices` |
| Display Names in English in a non-English environment | Use the environment's primary language for Display Names |
| Changing the schema without confirming the target URL and the `az` account | Confirm both with the user first |

## Skill boundaries

This skill covers Dataverse schema domain orientation, repository layout, and the core naming rule. It does not cover:

- Procedures that create or change schema objects → `dataverse:dv-metadata`
- Reviewing a model → `ppbp-dv-metadata-review`
- Table naming details, ownership, primary name column → `ppbp-dv-tables`
- Column naming and type conventions → `ppbp-dv-columns`
- Global Choice naming and solution integration → `ppbp-dv-global-choices`
- Forms, views, N:N relationships, calculated columns → `dataverse:dv-metadata`
- Connection setup and diagnostics → `dataverse:dv-connect`
- Project repository layout → `ppbp-overview`
