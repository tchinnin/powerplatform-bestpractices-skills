---
name: ppbp-dv-metadata
description: >
  Use when the user is designing, reviewing, or modifying a Dataverse data model:
  naming tables, columns, or relationships; choosing column types; defining option sets;
  or reviewing schema objects for convention compliance.
  Covers naming conventions (display vs. schema names, language rules, type-specific suffixes)
  and schema design best practices (relationships, cascade, column limits, option sets).
license: MIT
metadata:
  author: powerplatform-bestpractices
  version: "2.0"
---

## Naming conventions

**Core rule:** functional names (Display Name, Description) are always in the **environment's primary language** to leverage native Dataverse translations. Technical names (schema name) are always in **English**.

| Name type   | Language                        | Audience                       |
|-------------|----------------------------------|--------------------------------|
| Display Name | Environment's primary language  | End users                      |
| Description  | Environment's primary language  | End users / makers             |
| Schema Name  | English                         | Developers, integrations, code |

**Why:** Dataverse manages label translations natively via translation solution files. Keeping labels in the primary language prevents inconsistencies on export/import. English schema names guarantee code readability regardless of environment language.

### Tables

- **Display Name:** functional, not technical. **Singular** — Dataverse auto-generates the plural.
  - **DO:** `Order`, `Customer`, `Invoice`
  - **DO NOT:** `Orders`, `tbl_Order`, `Commande` (in an EN environment)
- **Description:** fill it in whenever possible. Functional framing (what the table does for the business), not technical.
- **Schema Name:** in a **shared environment** (multiple projects under the same publisher), prefix with a project code to avoid collisions:

  ```
  {PublisherPrefix}_{ProjectCode}_{TableName}
  ```

  Example — publisher `prfx`, project `code`, table `Order` → `prfx_code_Order`.

### Columns

- **Display Name:** functional, not technical.
- **Description:** fill in whenever possible. Functional.
- **Schema Name rules:**
  - **No project code prefix** — the parent table already carries the project context.
  - **No junction words** (`of`, `for`, `the`, …).
  - Stay **concise but explicit**.
  - Apply type-specific suffix/prefix conventions:

| Column type        | Convention                        | Example                                    |
|--------------------|-----------------------------------|--------------------------------------------|
| Lookup             | Suffix `Id`                       | `prfx_CustomerId`                          |
| Choice (OptionSet) | Suffix `Code`                     | `prfx_StatusCode`                          |
| Boolean            | Prefix Verb (e.g. `Is`, `Has`)    | `prfx_IsActive`, `prfx_HasApproval`        |
| Other types        | No specific convention            | `prfx_OrderDate`, `prfx_Amount`            |

### Global Choices

**DO NOT** use local option sets. **Always** use global Choices.

- **Display Name:** functional, ends with ` Choice`.
  - **DO:** `Project Status Choice`, `Invoice Type Choice`
  - **DO NOT:** `ProjectStatus`, `Status` (ambiguous, no type marker)
- **Description:** fill in whenever possible. Functional.
- **Schema Name:** contains `_choice_` as a type segment. In a shared environment, include the project code:

  ```
  {PublisherPrefix}_choice_{ChoiceName}           — single-project environment
  {PublisherPrefix}_{ProjectCode}_{ChoiceName}    — shared environment
  ```

  Example — `Project Status Choice` → `prfx_choice_ProjectStatus` (or `prfx_code_ProjectStatus` in a shared environment).

- **Translations:** use native Dataverse translations to localise choice labels — never duplicate a global Choice to work around language differences.

### Primary Name Column

If the table **has no meaningful text-based primary identifier** (junction table, technical table, non-textual natural key):

→ **Change the Primary Name Column type to AutoNumber.**

**Why:** the primary name column is mandatory and displayed everywhere (lookups, views, search). An empty or non-significant text column degrades UX and breaks search. AutoNumber guarantees a unique, readable value and eliminates visual duplicates in lookups.

---

## Schema design best practices

1. **Prefix all custom tables and columns** with a publisher prefix (e.g. `prfx_`) to avoid collisions with future OOB fields.
2. **Prefer lookup columns over manual foreign keys** — Dataverse enforces referential integrity and generates OData navigation properties automatically.
3. **Always use global Choices — never local option sets** — enables cross-table filtering and centralised translation management.
4. **Never store calculated values in regular columns** unless they must be queried with FetchXML; use Calculated or Rollup columns so values stay consistent without custom code.
5. **Design for the security model first** — row ownership (User vs. Team) determines cascade behaviour and directly impacts role design.
6. **Limit N:N relationships to truly many-to-many scenarios** — a manual junction table with extra columns is often better because it can carry metadata (status, date, etc.).
7. **Set meaningful `DisplayName` and `Description` on every object** — these surface in Power Apps and Copilot Studio without code.

## Common pitfalls

**Cascade delete on lookup** — Default "Parental" cascade deletes all child records when the parent is deleted, which is rarely intended. *Set cascade behaviour explicitly on every relationship; default to "Remove Link" unless cascading delete is required.*

**Overloading the primary name column** — `PrimaryName` is indexed and shown in lookups; treating it as a free-text description field causes poor lookup UX. *Keep it short and unique; use a separate Description column for long text.*

**Wrong column type for numeric IDs** — Whole Number columns max out at Int32; use Decimal or String for identifiers that may exceed 2 billion or contain leading zeros.

**Polymorphic lookups (Customer column)** — The built-in Customer column looks up both Account and Contact; using this pattern for custom tables requires extra API handling. *Create explicit lookups to each target table unless you need the OOB Customer column.*

**Ignoring the 400-column limit** — Dataverse tables are capped at 400 columns (including system columns). *Decompose wide tables into related 1:1 tables early.*
