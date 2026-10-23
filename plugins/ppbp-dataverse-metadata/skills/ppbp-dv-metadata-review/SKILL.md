---
name: ppbp-dv-metadata-review
description: >
  Read-only quality review of a Dataverse data model against the ppbp schema conventions,
  with a report ranked by severity (error / best practice / suggestion). Accepts any
  input: .dv.metadata.yaml files, dataverse/model docs, an exported solution's
  customizations.xml, a metadata dump, or pasted content. Use when the user wants to
  review, audit or challenge a Dataverse model — table design, column types, global
  Choices, lookups and cascade behaviour, ownership, auditing — before applying it or
  on an existing environment.
license: MIT
user-invocable: true
model: sonnet
allowed-tools: Read, Bash, Grep, Glob, WebSearch
metadata:
  author: powerplatform-bestpractices
  version: "1.0.0"
---

## Official skill

`dataverse:dv-metadata` — owns how Dataverse metadata is created, inspected and modified. Load it before this skill. If it is not installed, **strongly recommend the user install it** before proceeding. This skill only judges a model; it never changes one.

## What this skill adds

The `validate` command and the hook (`ppbp-dv-metadata-as-code`) catch mechanical errors. This skill covers the **judgement** a machine can't make: whether the column type fits the business meaning, whether a Choice is really closed, whether a lookup should cascade, whether the ownership and security model make sense, and whether the model is documented.

**Rule source:** the sibling skills are the only corpus. Read them before reviewing, and do not invent rules:

| Area | Source |
|---|---|
| Naming language, global principles | `ppbp-dv-metadata-overview` |
| Tables, ownership, primary column, cascade, security | `ppbp-dv-tables` |
| Column naming and type selection (incl. `money`, auditing) | `ppbp-dv-columns` |
| Global Choices | `ppbp-dv-global-choices` |

If you find a real problem that no rule covers, report it as 💡 and suggest adding it to the right sibling skill.

## Procedure

1. **Normalise the input.** Whatever format you're given, build one view: tables (ownership, primary column), columns (type, constraints, description), global Choices (options), lookups (target, cascade) and keys. If the scope isn't given, look for `dataverse/metadata/**/*.dv.metadata.yaml` with Glob. Don't query an environment and don't export solutions; that's not this skill's job. If there's nothing to review, ask for the model.
2. **Announce the scope:** *"Reviewing N tables, M global Choices from <source>."*
3. **Apply every rule** from the sources above. Rules tied to a file format (for example "`key` equals the file name") apply only when that format is the input.
4. **Report**, sorted by severity, with one concrete fix per finding:

```
Dataverse model review — dataverse/metadata — 4 tables, 3 Choices

❌ Errors (fix before apply)
  • prfx_crm_Order.prfx_Status — type text for a closed list of values
    Rule (ppbp-dv-columns): closed lists are global Choices.
    → type: choice + choice: prfx_crm_choice_OrderStatus

⚠️ Best practices
  • prfx_crm_Order.prfx_CustomerId — on_delete cascade on a non-composition link
    Rule (ppbp-dv-tables): explicit cascade, default removelink/restrict.
    → on_delete: restrict

💡 Suggestions
  • prfx_crm_choice_OrderStatus — options without colors.

Summary: 1 error, 1 best practice, 1 suggestion.
```

Severity:

| Level | Meaning |
|---|---|
| ❌ Error | Breaks a hard rule. The model shouldn't be applied as it is. |
| ⚠️ Best practice | Breaks a convention. Fix it unless there's an explicit justification. |
| 💡 Suggestion | Optional improvement. |

5. **Hand off.**
   - If the model came from `dataverse/metadata/`, fixes go through `ppbp-dv-metadata-as-code` and the `ppbp-dv-metadata-planner` agent.
   - If it came from an existing environment or solution, present the report as findings. Point out that some fixes, such as ownership, column type or primary column, can't be applied in place.

## Anti-patterns (DO NOT DO)

| Anti-pattern | Correct approach |
|---|---|
| Editing the model or running `plan`/`apply` during a review | Review is read-only; route fixes to `ppbp-dv-metadata-as-code` |
| Reporting conventions that are respected | Report real deviations only — no false positives |
| Raising a 💡 to ❌ to push a preference | Keep the severity the source skill implies |
| Inventing rules that aren't in the sibling skills | Report as 💡 and propose adding the rule to the right skill |
| Fetching metadata from an environment yourself | Ask the user for the input, or use the repo model |

## Skill boundaries

- Domain orientation and repository layout → `ppbp-dv-metadata-overview`
- Writing or changing the model, plan/apply → `ppbp-dv-metadata-as-code`
- Exporting a solution to review it → `dataverse:dv-solution`
- Inspecting live metadata → `dataverse:dv-metadata`
