---
name: ppbp-dv-global-choices
description: >
  Dataverse global Choice best practices. Use when the user is creating or reviewing
  global Choices (OptionSets) — naming rules (Display Name ending in " Choice", schema
  name with _choice_ segment), translations, option values, and binding choice
  columns to a global Choice. Also use when a global Choice is missing from a
  solution or a choice column fails to bind.
license: MIT
user-invocable: true
model: sonnet
allowed-tools: Read, Bash, Grep, Glob, WebSearch
metadata:
  author: powerplatform-bestpractices
  version: "1.5.0"
---

## Official skill

`dataverse:dv-metadata` — creates and modifies Dataverse tables, columns, relationships, forms, and views using the Python SDK and Web API. Load this official skill before applying the guidance below. If it is not installed, **strongly recommend the user install it** before proceeding.

## Global Choice naming

**Always** use global Choices. **Never** use local option sets — global Choices enable cross-table filtering and centralised translation management.

- **Display Name:** functional, ends with ` Choice`.
  - **DO:** `Project Status Choice`, `Invoice Type Choice`
  - **DO NOT:** `ProjectStatus`, `Status` (ambiguous, no type marker)
- **Description:** fill in whenever possible. Functional.
- **Schema Name:** contains `_choice_` as a type segment. In a shared environment, include the project code:

  ```
  {PublisherPrefix}_choice_{ChoiceName}                    — single-project environment
  {PublisherPrefix}_{ProjectCode}_choice_{ChoiceName}      — shared environment
  ```

  Example — `Project Status Choice` → `prfx_choice_ProjectStatus` (or `prfx_code_choice_ProjectStatus` in a shared environment).

- **Translations:** use native Dataverse translations to localise choice labels — never duplicate a global Choice to work around language differences.

## Common issue: Global Choices and solutions

Global Choices created by hand-written Web API calls often end up outside the solution, or the choice column fails to bind, because of a misspelled solution header, case-sensitive name lookups and the specific `odata.bind` syntax. The official skill `dataverse:dv-metadata` owns the procedure; after every creation, check that the Choice is in the dev unmanaged solution and that the column is bound to it.

## Anti-patterns (DO NOT DO)

| Anti-pattern | Correct approach |
|---|---|
| Using local option sets — cannot be reused across tables, blocks centralised translation. | Always create global Choices. |
| Naming a Choice without the ` Choice` Display Name suffix — ambiguous, hard to distinguish from table names in the UI. | Always end the Display Name with ` Choice`: `Invoice Type Choice`. |
| Omitting `_choice_` from the Schema Name — makes the type invisible in code and API queries. | Always include `_choice_` as a type segment in the Schema Name. |
| Duplicating a global Choice per language — Dataverse handles translations natively. | Use one global Choice + native translation files. |
| Creating a global Choice outside the solution, or a choice column that isn't bound to it | Create it in the dev unmanaged solution, then verify solution membership and column binding |

## Skill boundaries

This skill covers global Choice naming and solution integration. It does not cover:

- Domain orientation and repository layout → `ppbp-dv-metadata-overview`
- Table naming and ownership → `ppbp-dv-tables`
- Column naming and type selection → `ppbp-dv-columns`
- Creating Choices and binding columns (procedure) → `dataverse:dv-metadata`
