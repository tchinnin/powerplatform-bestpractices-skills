---
name: ppbp-dv-metadata-as-code
description: >
  Dataverse metadata as code: global Choices, tables, columns, lookups and alternate
  keys are described in dataverse/metadata/*.dv.metadata.yaml and reconciled with the
  dev environment through a Terraform-style plan → confirm → apply loop that never
  deletes. Use when the user wants to create or change Dataverse tables, columns,
  Choices, lookups or keys, write or fix .dv.metadata.yaml files, preview schema
  changes (plan), apply the model, or detect drift between the model and the
  environment.
license: MIT
user-invocable: true
model: sonnet
allowed-tools: Read, Write, Edit, Bash, Grep, Glob, WebSearch
argument-hint: "<schema change request>"
metadata:
  author: powerplatform-bestpractices
  version: "1.0.1"
---

## Official skill

`dataverse:dv-metadata` owns how Dataverse metadata is created and modified (SDK, Web API, solution headers, publishing, error codes). Load it before this skill. If it is not installed, **strongly recommend the user install it** before proceeding. This skill adds a declarative model and the tooling that reconciles it. It does not restate the official procedures.

## What this skill adds

- **One declarative model.** The YAML files under `dataverse/metadata/` are the source of truth for the schema. The layout and the precedence over `dataverse/model/*.md` are defined in `ppbp-dv-metadata-overview`.
- **One tool**, `scripts/dv_metadata.py`, with four subcommands:

| Subcommand | Touches the server | Purpose |
|---|---|---|
| `doctor [model-dir]` | read | Checks deps, the `az` session, the dev guard and that the solution is unmanaged |
| `validate <dir\|file>` | no | Structural (JSON Schema) + semantic checks (naming, references, conventions) |
| `plan <model-dir> [--json]` | read | Diff → `+ create` / `~ update` (field `old → new`) / `! blocked` / `? unmanaged` |
| `apply <model-dir> --plan-file <f>` | write | Runs exactly the saved plan. Aborts if the plan is stale. Never deletes. |

- **A PostToolUse hook** (Claude Code). It runs `validate` after every edit to a `*.dv.metadata.yaml` file and returns errors to the agent right away. On GitHub Copilot, run `validate` explicitly.
- **A planner agent**, `ppbp-dv-metadata-planner`, that runs the whole loop with a user confirmation gate.

Run the script from the plugin's skill folder: `python3 <this-skill>/scripts/dv_metadata.py …`. Install its dependencies first with `pip install -r <this-skill>/scripts/requirements.txt`, inside a venv.

## Workflow: plan → confirm → apply

Delegate schema changes to the **`ppbp-dv-metadata-planner`** agent. It runs in two invocations:

1. **Planning run.** The agent edits the YAML model and the matching `dataverse/model/<domain>.md`, validates them, runs `plan`, and returns:
   - the target environment and solution
   - every create, update, blocked and unmanaged item
   - the items that need double confirmation
2. **The main thread shows that plan to the user.** Ask for explicit confirmation of the environment and of the exact change list. Ask **twice** for each item that needs double confirmation:
   - Organization-owned tables
   - `money` columns
   - auditing turned on
3. **Apply run.** Re-invoke the agent with `approved: <plan file>`. It runs `apply`, then checks that the follow-up plan is empty.

Never run `apply` without a plan the user has just seen. Never apply a plan that contains blocked items.

## Model files

```yaml
# dataverse/metadata/_meta.dv.metadata.yaml
version: "1.0"
publisher:
  prefix: prfx
  project_code: crm        # optional — when set, tables and Choices are prfx_crm_…
  solution: prfx_crm_Core  # unmanaged solution in dev
locale: en
```

- `choices.dv.metadata.yaml` holds every global Choice.
- `tables/<key>.dv.metadata.yaml` holds one table per file, and the file name must equal `key`.
- YAML keys are **Schema Names**. The naming conventions they follow are in `ppbp-dv-tables`, `ppbp-dv-columns` and `ppbp-dv-global-choices`, and the validator enforces them.
- Every attribute, per column type, is listed in [`references/format.md`](references/format.md). Annotated samples are in [`references/samples/`](references/samples/).
- Attributes you leave out of the YAML are **not managed**. The tool never resets them on the server. The exceptions are `label`, `type`, `required`/`required_level` and table `auditing`, which always have a managed default.

## Safety model

- **Dev only, enforced by the tool.** It reads only `<repo-root>/.env.dev` (created by `ppbp-init`), and refuses to run unless all of these hold:
  - `ENVIRONMENT_STAGE=dev`
  - the URL differs from the ones in `.env.uat` and `.env.prod`
  - the model's solution exists **and is unmanaged**

  This enforces the ALM rule in `ppbp-alm-overview`: UAT and prod only receive managed imports. There is no flag to override the guard.
- **Azure CLI token.** The tool authenticates with the developer's `az login` session. Use `az login --tenant <TENANT_ID>` when the account spans several tenants. Prerequisites and fixes are in [`references/prerequisites.md`](references/prerequisites.md).
- **Never destructive.** Changes that would need a delete or recreate are `! blocked`. Server components that aren't in the model are `? unmanaged`, reported only. Removing anything is a manual, deliberate act outside this tool.

## Common issue: stale plan

`apply` recomputes the plan and aborts if it differs from the saved file. This happens when someone changed the model or the environment after `plan`. Re-run `plan` and get the user's confirmation again. See [`references/plan-apply.md`](references/plan-apply.md).

## Common issue: blocked changes

A column type change, a change of bound Choice, an ownership change or a primary-column change cannot be applied in place. Either revert the YAML to match the server, or plan a new column plus a data migration. The full list and the alternatives are in [`references/plan-apply.md`](references/plan-apply.md).

## Common issue: changes made in the maker portal

A change made directly in the environment shows up as `~ update` (the model would revert it) or as `? unmanaged`. Bring the change into the YAML **before** applying, or the next apply overwrites it.

## Anti-patterns (DO NOT DO)

| Anti-pattern | Correct approach |
|---|---|
| Writing ad-hoc Python/PowerShell scripts that create tables or columns | Describe the change in `dataverse/metadata/` and run plan → apply |
| Running `apply` without showing the plan to the user, or reusing an old plan | Plan, show it, get confirmation, then apply that plan file |
| Pointing the tool at UAT/prod by editing `.env.dev` or copying URLs | Only dev holds the unmanaged solution; promote through the ALM pipeline (`ppbp-alm-pipelines`) |
| Deleting server components that the plan reports as unmanaged | Either add them to the model or remove them manually after a deliberate decision — never from the agent |
| Editing `dv_metadata.py` or the JSON Schemas in a project | Edit only the model files; propose tooling changes upstream |
| Changing the YAML without updating `dataverse/model/<domain>.md` | Update both in the same change — the `.md` is the review view |
| Inline option lists on a choice column | Reference a global Choice with `choice:` (`ppbp-dv-global-choices`) |

## Skill boundaries

- Domain orientation and repository layout → `ppbp-dv-metadata-overview`
- Table, column and global Choice conventions → `ppbp-dv-tables`, `ppbp-dv-columns`, `ppbp-dv-global-choices`
- Quality review of a model → `ppbp-dv-metadata-review`
- Forms, views, N:N relationships, calculated/rollup/formula columns → `dataverse:dv-metadata` (outside this model)
- Solution creation, export, pull-to-repo → `dataverse:dv-solution`
- Promotion to UAT/prod → `ppbp-alm-pipelines`
