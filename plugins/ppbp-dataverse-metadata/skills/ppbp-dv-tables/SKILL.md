---
name: ppbp-dv-tables
description: >
  Dataverse table design best practices. Use when the user is creating or reviewing
  tables — naming rules (Display Name singular, Schema Name with publisher prefix,
  project code in shared environments), table ownership (User Owned vs. Organization
  Owned), primary name column configuration, AutoNumber, cascade behaviour, or
  wide-table decomposition. Also use when the user asks about publisher prefix or
  table description conventions.
license: MIT
metadata:
  author: powerplatform-bestpractices
  version: "1.1.0"
---

## Official skill

`dataverse:dv-metadata` — creates and modifies Dataverse tables, columns, relationships, forms, and views using the Python SDK and Web API. Load this official skill before applying the guidance below. If it is not installed, **strongly recommend the user install it** before proceeding.

## Table naming

- **Display Name:** functional, not technical. **Singular** — Dataverse auto-generates the plural.
  - **DO:** `Order`, `Customer`, `Invoice`
  - **DO NOT:** `Orders`, `tbl_Order`, `Commande` (in an EN environment)
- **Description:** fill it in whenever possible. Functional framing (what the table does for the business), not technical.
- **Schema Name:** in a **shared environment** (multiple projects under the same publisher), prefix with a project code to avoid collisions:

  ```
  {PublisherPrefix}_{ProjectCode}_{TableName}
  ```

  Example — publisher `prfx`, project `code`, table `Order` → `prfx_code_Order`.

## Primary Name Column

If the table **has no meaningful text-based primary identifier** (junction table, technical table, non-textual natural key):

→ **Change the Primary Name Column type to AutoNumber.**

**Why:** the primary name column is mandatory and displayed everywhere (lookups, views, search). An empty or non-significant text column degrades UX and breaks search. AutoNumber guarantees a unique, readable value and eliminates visual duplicates in lookups.

## Table ownership

**Default: always User Owned.** Every new table must use `UserOwned` ownership unless the user explicitly requests otherwise.

- **User Owned** — rows are owned by a specific user or team; security roles apply at row level. This is the correct default for all business data.
- **Organization Owned** — rows are owned by the entire org; no row-level security is possible. Use only when every user in the org must always see every row and row-level access control is permanently off the table.

**Runtime guard — Organization Owned requires double confirmation.** If a script you are about to execute creates a table with `OrganizationOwned` ownership, you **must** stop and ask the user to confirm twice before running it:

1. First confirmation: *"This script will create a table with Organization Owned ownership — all users will have full visibility of every row, with no row-level security. Is that intentional?"*
2. Second confirmation: *"Confirmed: you want Organization Owned, not User Owned?"*

Only proceed if the user explicitly confirms both times.

> **Why:** changing a table's ownership type after data has been loaded requires recreating the table and migrating all records — it cannot be altered in place. Defaulting to the wrong ownership is a costly mistake.

## Schema design best practices

1. **Prefix all custom tables** with a publisher prefix (e.g. `prfx_`) to avoid collisions with future OOB fields.
2. **Prefer lookup columns over manual foreign keys** — Dataverse enforces referential integrity and generates OData navigation properties automatically.
3. **Never store calculated values in regular columns** unless they must be queried with FetchXML; use Calculated or Rollup columns so values stay consistent without custom code.
4. **Design for the security model first** — row ownership (User vs. Team) determines cascade behaviour and directly impacts role design.
5. **Limit N:N relationships to truly many-to-many scenarios** — a manual junction table with extra columns is often better because it can carry metadata (status, date, etc.).
6. **Set meaningful `DisplayName` and `Description` on every table** — these surface in Power Apps and Copilot Studio without code.

## Anti-patterns (DO NOT DO)

| Anti-pattern | Correct approach |
|---|---|
| Organization Owned by default — removing row-level security is irreversible without a full table rebuild; it is almost never the right choice for business data. | Default to User Owned; only use Organization Owned when the user explicitly requests it, with double confirmation before executing. |
| Leaving cascade behaviour implicit on a relationship — an unintended cascade delete can wipe child records when the parent is removed. | Set cascade behaviour explicitly on every relationship; default to "Remove Link" unless a cascading delete is genuinely required. |
| Overloading the primary name column — `PrimaryName` is indexed and shown in lookups; treating it as a free-text description field causes poor lookup UX. | Keep it short and unique; use a separate Description column for long text. |
| Building excessively wide tables — very wide tables hit Dataverse's per-row size limit and degrade query and form performance. | Decompose wide tables into related 1:1 tables early. |

## Skill boundaries

This skill covers Dataverse table design only. It does not cover:

- Domain orientation and repository layout → `ppbp-dv-metadata-overview`
- Column naming conventions and type selection → `ppbp-dv-columns`
- Global Choices → `ppbp-dv-global-choices`
- Writing or registering plug-in steps or Custom APIs → `ppbp-dv-plugins-overview`
- Solution lifecycle, environment strategy, deployment pipelines → `ppbp-alm-solutions`
