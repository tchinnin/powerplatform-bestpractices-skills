---
name: ppbp-dv-columns
description: >
  Dataverse column design best practices. Use when the user is creating or reviewing
  columns — naming rules (Display Name, Schema Name, no project code prefix), type-specific
  suffix and prefix conventions (Lookup Id, Choice Code, Boolean Is/Has), column type
  selection, local option sets vs. global Choices, polymorphic lookups, or numeric ID
  column types. Also use when the user asks about column description conventions or
  publisher prefix on columns.
license: MIT
metadata:
  author: powerplatform-bestpractices
  version: "1.1.0"
---

## Official skill

`dataverse:dv-metadata` — creates and modifies Dataverse tables, columns, relationships, forms, and views using the Python SDK and Web API. Load this official skill before applying the guidance below. If it is not installed, **strongly recommend the user install it** before proceeding.

## Column naming

- **Display Name:** functional, not technical.
- **Description:** fill in whenever possible. Functional.
- **Schema Name rules:**
  - **No project code prefix** — the parent table already carries the project context.
  - **No junction words** (`of`, `for`, `the`, …).
  - Stay **concise but explicit**.
  - Apply type-specific suffix/prefix conventions:

| Column type | Convention | Example |
|---|---|---|
| Lookup | Suffix `Id` | `prfx_CustomerId` |
| Choice (OptionSet) | Suffix `Code` | `prfx_StatusCode` |
| Boolean | Prefix verb (`Is`, `Has`) | `prfx_IsActive`, `prfx_HasApproval` |
| Other types | No specific convention | `prfx_OrderDate`, `prfx_Amount` |

> **Only lookup columns take the `Id` suffix.** A regular (non-lookup) column must never end in `Id` — it collides with the navigation property Dataverse auto-generates for lookups. For a business identifier on a regular column, use a different stem (e.g. `prfx_SourceRef`, not `prfx_SourceId`). See `dataverse:dv-metadata` for the underlying rule.

## Schema design best practices

1. **Prefix all custom columns** with a publisher prefix (e.g. `prfx_`) to avoid collisions with future OOB fields.
2. **Always use global Choices — never local option sets** — enables cross-table filtering and centralised translation management. See `ppbp-dv-global-choices` for naming and solution integration.
3. **Set meaningful `DisplayName` and `Description` on every column** — these surface in Power Apps and Copilot Studio without code.

## Anti-patterns (DO NOT DO)

| Anti-pattern | Correct approach |
|---|---|
| Wrong column type for numeric IDs — Whole Number columns max out at Int32 (~2 billion). | Use Decimal or String for identifiers that may exceed 2 billion or contain leading zeros. |
| Polymorphic lookups (Customer column) — The built-in Customer column looks up both Account and Contact; using this pattern for custom tables requires extra API handling. | Create explicit lookups to each target table unless you need the OOB Customer column. |
| Using local option sets instead of global Choices — Local option sets cannot be reused across tables and block centralised translation. | Always create a global Choice; see `ppbp-dv-global-choices` for the correct procedure. |
| Adding project code prefix to column Schema Name — The parent table already scopes the column to the project. | Omit the project code prefix on columns; apply it only at the table level. |

## Skill boundaries

This skill covers Dataverse column naming and type selection. It does not cover:

- Domain orientation, repository layout, and core naming rule → `ppbp-dv-metadata-overview`
- Table naming, ownership, and primary name column → `ppbp-dv-tables`
- Global Choices naming, schema, and solution integration → `ppbp-dv-global-choices`
- Writing or deploying schema scripts → `dataverse:dv-metadata`
- Plugin or Custom API development → `ppbp-dv-plugins-overview`
