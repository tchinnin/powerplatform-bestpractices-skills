# ppbp-dataverse-metadata — Agent Orchestration

## Purpose

This plugin covers Dataverse schema design best practices: the naming split between Display Name (primary language) and Schema Name (English), table ownership decisions, column type suffixes, publisher prefix usage, and global Choice conventions. It adds opinionated team policies on top of the official `dataverse:dv-metadata` skill.

## Skill load order

Load `ppbp-dv-metadata-overview` first — it contains the core naming rule and global principles shared by all three task skills. Then load the task skill matching the current work. For global Choices in a solution context, the `references/global-choices-in-solutions.md` file carries the full AddSolutionComponent procedure — load it before writing any script.

## Routing logic

| User intent | Skill to invoke |
|---|---|
| "Create a table" / "design schema" | `ppbp-dv-metadata-overview`, then `ppbp-dv-tables` |
| "Add columns to a table" | `ppbp-dv-columns` |
| "Create a global Choice / option set" | `ppbp-dv-global-choices` |
| "Write a schema script" | Official `dataverse:dv-metadata` |
| "Connect to Dataverse" | Official `dataverse:dv-connect` |

## Constraints

The paired official skill is `dataverse:dv-metadata`. Verify it is active before invoking any skill in this plugin. Connection setup is owned by `dataverse:dv-connect` — always confirm the active environment via that skill before running any schema script. The global-Choices-in-solutions issue (AddSolutionComponent) is documented in `ppbp-dv-global-choices/references/global-choices-in-solutions.md`.
