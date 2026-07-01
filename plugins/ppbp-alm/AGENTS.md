# ppbp-alm — Agent Orchestration

## Purpose

This plugin covers Application Lifecycle Management best practices for Power Platform: solution design, naming conventions, segmentation layers, dependency ordering, versioning strategy, and deployment pipelines. It adds opinionated team conventions on top of the official PAC CLI-based solution management workflow.

## Skill load order

Always load `ppbp-alm-overview` first — it sets the conventions that both task skills depend on. Then load `ppbp-alm-solutions` for solution structure and naming decisions, or `ppbp-alm-pipelines` for deployment pipeline configuration.

## Routing logic

| User intent | Skill to invoke |
|---|---|
| "How should I structure my solutions?" | `ppbp-alm-overview`, then `ppbp-alm-solutions` |
| "What naming should I use for solutions?" | `ppbp-alm-solutions` |
| "Set up a deployment pipeline" | `ppbp-alm-pipelines` |
| "How do I export/import solutions?" | Official `dataverse:dv-solution` skill |

## Constraints

The paired official skill is `dataverse:dv-solution`. Verify it is active before invoking any skill in this plugin. The ppbp-alm skills add conventions the official skill does not cover — they do not repeat PAC CLI syntax or deployment procedures, which are owned by the official skill.
