---
name: ppbp-dv-global-choices
description: >
  Dataverse global Choice best practices. Use when the user is creating or reviewing
  global Choices (OptionSets) — naming rules (Display Name ending in " Choice", schema
  name with _choice_ segment), translations, binding a Picklist column to a global
  Choice, or adding a global Choice to a solution. Also use when the user encounters
  errors like "Choice not found in solution" or "odata.bind syntax" when creating
  OptionSet columns.
license: MIT
metadata:
  author: powerplatform-bestpractices
  version: "1.1.0"
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

Creating a Global Choice via the Web API does **not** add it to a solution automatically — a second `AddSolutionComponent` call (ComponentType 9) is required. Binding a Picklist column to a global choice also requires a specific `odata.bind` syntax that differs from local option sets.

If you are scripting Global Choices in a solution context, load [`references/global-choices-in-solutions.md`](references/global-choices-in-solutions.md) before writing any code.

## Anti-patterns (DO NOT DO)

| Anti-pattern | Correct approach |
|---|---|
| Using local option sets — cannot be reused across tables, blocks centralised translation. | Always create global Choices. |
| Naming a Choice without the ` Choice` Display Name suffix — ambiguous, hard to distinguish from table names in the UI. | Always end the Display Name with ` Choice`: `Invoice Type Choice`. |
| Omitting `_choice_` from the Schema Name — makes the type invisible in code and API queries. | Always include `_choice_` as a type segment in the Schema Name. |
| Duplicating a global Choice per language — Dataverse handles translations natively. | Use one global Choice + native translation files. |
| Binding a Picklist column using local option set syntax — causes a schema mismatch error when binding to a global Choice. | Use `GlobalOptionSet@odata.bind` syntax; see [`references/global-choices-in-solutions.md`](references/global-choices-in-solutions.md). |

## Skill boundaries

This skill covers global Choice naming and solution integration. It does not cover:

- Table naming and ownership → `ppbp-dv-tables`
- Column naming and type selection → `ppbp-dv-columns`
- Writing or deploying schema scripts → `dataverse:dv-metadata`
