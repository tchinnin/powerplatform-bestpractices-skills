---
name: ppbp-dv-metadata
description: >
  Use when the user is designing, reviewing, or modifying a Dataverse data model:
  creating or updating tables, columns, relationships (1:N, N:N, polymorphic),
  defining option sets, choosing column types, or naming schema objects.
  Applies Power Platform best practices for schema design and common pitfalls.
license: MIT
metadata:
  author: powerplatform-bestpractices
  version: "1.0"
---

## Best practices

1. **Prefix all custom tables and columns** with a publisher prefix (e.g. `tch_`) to avoid collisions with future OOB fields.
2. **Prefer lookup columns over manual foreign keys** — Dataverse enforces referential integrity and generates OData navigation properties automatically.
3. **Use Choice/Choices columns (global option sets) over local option sets** when the same values appear in more than one table — it enables cross-table filtering.
4. **Never store calculated values in regular columns** unless they must be queried with FetchXML; use Calculated or Rollup columns so values stay consistent without custom code.
5. **Design for the security model first** — row ownership (user vs. team) determines cascade behaviour and directly impacts role design.
6. **Limit N:N relationships to truly many-to-many scenarios**; a manual junction table with extra columns is often better because it can carry metadata (e.g. status, date).
7. **Keep table names singular** (`tch_Order`, not `tch_Orders`) — Dataverse pluralises automatically in the API.
8. **Set meaningful `DisplayName` and `Description` on every object** — these surface in Power Apps and Copilot Studio without code.

## Common pitfalls

**Cascade delete on lookup** — Default "Parental" cascade on a lookup will delete all child records when the parent is deleted, which is rarely the intended behaviour. *Set cascade behaviour explicitly on every relationship; default to "Remove Link" unless you need cascading delete.*

**Overloading the primary name column** — The `PrimaryName` column is indexed and shown in lookups; treating it as a free-text description field causes poor lookup UX. *Keep it short and unique; use a separate Description column for long text.*

**Using the wrong column type for numeric IDs** — Whole Number columns max out at Int32; use Decimal or String for identifiers that may exceed 2 billion or contain leading zeros.

**Polymorphic lookups (Customer column)** — The built-in Customer column looks up both Account and Contact. Using this pattern for custom tables requires extra API handling. *Create explicit lookups to each target table unless you need the OOB Customer column.*

**Ignoring the 400 column limit** — Dataverse tables are capped at 400 columns (including system columns). *Decompose wide tables into related 1:1 tables early.*
