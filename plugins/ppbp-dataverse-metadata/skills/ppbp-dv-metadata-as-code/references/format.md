# `.dv.metadata.yaml` format reference

The JSON Schemas in [`schemas/`](schemas/) are authoritative. This page explains them. Annotated examples are in [`samples/`](samples/).

Every file starts with the `yaml-language-server` directive so VS Code validates it as you type:

```yaml
# yaml-language-server: $schema=<relative path to the skill>/references/schemas/table.schema.json
```

## Files

| File | Schema | Content |
|---|---|---|
| `_meta.dv.metadata.yaml` | `meta.schema.json` | `version`, `publisher.{prefix, project_code?, solution}`, `locale` |
| `choices.dv.metadata.yaml` | `choices.schema.json` | `choices:` map of global Choices |
| `tables/<key>.dv.metadata.yaml` | `table.schema.json` | One table, with its columns and alternate keys |

The tool finds table files with a glob over `tables/*.dv.metadata.yaml`. There is no manifest, and the tool works out the dependency order itself: Choices → tables → columns → lookups → keys.

## Names

| Object | Form | Example (`prefix: prfx`, `project_code: crm`) |
|---|---|---|
| Table | `{prefix}_[{project_code}_]{TableName}` | `prfx_crm_Order` |
| Global Choice | `{prefix}_[{project_code}_]choice_{ChoiceName}` | `prfx_crm_choice_OrderStatus` |
| Column | `{prefix}_{ColumnName}`, never with the project code | `prfx_CustomerId` |
| Alternate key | `{prefix}_…` | `prfx_crm_customer_customernumber_key` |

YAML keys are **Schema Names**, so their casing is kept. The tool compares names case-insensitively, the way Dataverse logical names work. References such as `choice:`, `target:` and key `columns:` may be written in either case.

## `_meta`

| Key | Required | Notes |
|---|---|---|
| `version` | yes | `"1.0"` |
| `publisher.prefix` | yes | 2–8 lowercase alphanumeric characters, permanent |
| `publisher.project_code` | no | When set, every table and Choice must carry it |
| `publisher.solution` | yes | Unique name of the **unmanaged** dev solution |
| `locale` | yes | `en`, `fr`, `es`, `de`, `it`, `pt` or `nl`. Display Names are written in this language (LCID). |

## Global Choice

```yaml
choices:
  prfx_crm_choice_OrderStatus:
    label: Order Status Choice      # ends with " Choice"
    description: Lifecycle of a customer order.
    options:
      - {value: 100000000, label: Draft, color: "#9EA6B3"}
      - {value: 100000001, label: Confirmed}
```

- Custom option values start at `100000000`. Values must be unique.
- `color` is applied **when the Choice is created** only. After that the API cannot change an option's color, so change it in the maker portal.
- An option you remove from the YAML is reported as `? unmanaged`. It is never deleted.

## Table

| Key | Default | Managed after creation |
|---|---|---|
| `key` | — (required) | — (identity) |
| `label` | — (required) | yes |
| `label_plural` | `label + "s"` at creation | only if declared |
| `description` | `label` at creation | only if declared |
| `ownership` | `user` | **blocked** if it differs |
| `table_type` | `standard` (`activity`, `elastic`) | **blocked** if it differs |
| `auditing` | `false` | yes |
| `columns` | — (required, exactly one `primary: true`) | see below |
| `keys` | none | create only; a change to a key's columns is **blocked** |

## Columns

Common attributes:

| Attribute | Applies to | Managed when |
|---|---|---|
| `label`, `type` | all | always (`type` change → **blocked**) |
| `required` / `required_level` | all | always; default `none` |
| `description`, `auditing`, `searchable` | all | only if declared |
| `primary` | text, autonumber | exactly one per table; it can't be changed later |

Type-specific attributes:

| `type` | Attributes | Notes |
|---|---|---|
| `text`, `email`, `url`, `phone` | `max_length` | text ≤ 4000 |
| `multiline` | `max_length` | |
| `autonumber` | `format` (required), `max_length` | e.g. `"ORD-{SEQNUM:6}"` |
| `integer` | `min`, `max` | Int32 — use decimal or text for IDs that can exceed it |
| `decimal` | `min`, `max`, `precision` | default type for amounts |
| `money` | `min`, `max`, `precision` | needs double confirmation (currency machinery) |
| `boolean` | `default` | Yes/No labels follow `locale` |
| `date` | — | date only |
| `datetime` | `behavior`: `userlocal` \| `timezoneindependent` | `userlocal` → another behavior is allowed once; anything else is **blocked** |
| `choice` | `choice` (required), `default` | `default` must be an option value |
| `multichoice` | `choice` (required) | |
| `lookup` | `target` (required), `on_delete` (required): `restrict` \| `removelink` \| `cascade` | creates the N:1 relationship `{table}_{ColumnName}`; `target` change → **blocked** |
| `file` | `max_size_kb` (default 32768) | size can't be changed later |
| `image` | `max_size_kb` | |

Calculated, rollup and formula columns, N:N relationships, forms and views are **outside the model**. Handle them with `dataverse:dv-metadata`.

## Alternate keys

```yaml
keys:
  - schema_name: prfx_crm_customer_customernumber_key
    columns: [prfx_customernumber]
    label: Customer Number Key
```

Dataverse builds the index asynchronously after creation.
