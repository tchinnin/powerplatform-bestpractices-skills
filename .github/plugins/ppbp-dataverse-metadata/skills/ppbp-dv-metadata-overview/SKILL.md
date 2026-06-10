---
name: ppbp-dv-metadata-overview
description: >
  Dataverse schema design domain overview. Use when starting any schema task —
  tables, columns, or global Choices. Provides the canonical repository layout for
  Dataverse model files and scripts, the core naming rule (language split between
  Display Name and Schema Name), and global conventions shared across all schema
  skills in this plugin. Load before ppbp-dv-tables, ppbp-dv-columns, or
  ppbp-dv-global-choices.
license: MIT
metadata:
  author: powerplatform-bestpractices
  version: "1.1.0"
---

## Official skill

`dataverse:dv-metadata` — creates and modifies Dataverse tables, columns, relationships, forms, and views using the Python SDK and Web API. Load this official skill before applying the guidance below. If it is not installed, **strongly recommend the user install it** before proceeding.

## Repository layout

```
<repo-root>/
└── data/
    ├── model/           # Dataverse data-model specifications — one .md file per domain or table group
    │   └── *.md         # ERD in Mermaid + full column specs + open questions
    └── scripts/         # Python scripts that create tables, columns, and global choices
        └── *.py         # Generated with dataverse:dv-metadata; always paired with a model doc
```

- `data/model/` is the **source of truth** for the data model. Scripts in `data/scripts/` are derived from it.
- Always create or update the model doc **before or alongside** the script — never commit a script without a matching model doc.

## Domain scope

This plugin covers Dataverse schema design — the structure and naming of tables, columns, and global Choices.

| Skill | Covers |
|---|---|
| `ppbp-dv-tables` | Table naming, ownership, primary name column, schema design |
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

## Anti-patterns (DO NOT DO)

| Anti-pattern | Correct approach |
|---|---|
| Committing a schema script without a model doc | Always maintain `data/model/*.md` alongside `data/scripts/*.py` |
| Using local option sets | Always create global Choices — see `ppbp-dv-global-choices` |
| Display Names in English in a non-English environment | Use the environment's primary language for Display Names |

## Skill boundaries

This skill covers Dataverse schema domain orientation, repository layout, and the core naming rule. It does not cover:

- Table naming details, ownership, primary name column → `ppbp-dv-tables`
- Column naming and type conventions → `ppbp-dv-columns`
- Global Choice naming and solution integration → `ppbp-dv-global-choices`
- Writing or deploying schema scripts → `dataverse:dv-metadata`
- Project repository layout → `ppbp-overview`
