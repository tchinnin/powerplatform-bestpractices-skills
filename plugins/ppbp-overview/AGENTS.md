# ppbp-overview — Agent Orchestration

## Purpose

This plugin provides project-level orientation for any Power Platform repository. It routes agents to the right domain plugin and ensures the canonical repository layout is followed from the first session. It contains no implementation guidance — it is the entry point that tells agents what exists and where to go.

## Skill load order

Load `ppbp-overview` automatically at the start of every session in a Power Platform project (declare it in the agent instruction file). Load `ppbp-init` only when starting a new project from scratch. Load `ppbp-readme` only when updating or creating README.md.

## Routing logic

| User intent | Skill to invoke |
|---|---|
| "How is this project structured?" | `ppbp-overview` |
| "Set up a new project" / "create CLAUDE.md" | `ppbp-init` |
| "Update README" / "write a README" | `ppbp-readme` |
| Any domain-specific task | Route to the relevant domain plugin |

## Constraints

No official Microsoft skill pairs with this plugin — it covers project orientation only, which is outside the scope of any official Power Platform skill. Skills in this plugin may be used standalone, without loading an official skill first.
