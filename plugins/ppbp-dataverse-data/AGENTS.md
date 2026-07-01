# ppbp-dataverse-data — Agent Orchestration

## Purpose

This plugin covers Dataverse data manipulation best practices: script naming and lifecycle conventions, idempotency requirements, the prereq/prod/dev/temp import folder structure, bulk operations, dependency ordering, and environment segmentation rules. It adds opinionated guidance on top of the official `dataverse:dv-data` skill.

## Skill load order

Load `ppbp-dv-data-overview` first to establish the folder structure and lifecycle conventions shared by both task skills. Then load `ppbp-dv-data-scripts` for script organisation and idempotency patterns, or `ppbp-dv-data-import` for bulk import and dependency ordering.

## Routing logic

| User intent | Skill to invoke |
|---|---|
| "Create a data script" / "how to organise scripts" | `ppbp-dv-data-overview`, then `ppbp-dv-data-scripts` |
| "Import data" / "load records" / "bulk insert" | `ppbp-dv-data-import` |
| "Write a Python Dataverse script" | Official `dataverse:dv-data` |
| "Connect to Dataverse" | Official `dataverse:dv-connect` |

## Constraints

The paired official skill is `dataverse:dv-data`. Verify it is active before invoking any skill in this plugin. Every script in `data/import/` must be idempotent — this is a hard constraint enforced by team convention, not just a best practice. Dev-only scripts in `data/import/dev/` must never run in production environments.
