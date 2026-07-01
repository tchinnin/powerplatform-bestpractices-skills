# ppbp-codeapps — Agent Orchestration

## Purpose

This plugin covers Power Apps Code Apps best practices: project scaffolding conventions, connector integration patterns, type generation discipline, bundle optimisation guidelines, UX/UI theming with Fluent v9, and deployment workflow. It adds opinionated guidance on top of the official `code-apps-preview` skill.

## Skill load order

Load `ppbp-codeapps-overview` first to establish conventions for the domain. Then load the specific task skill matching the current work. `ppbp-codeapps-uxui` has a `references/guidelines-and-theming.md` file — load it when working on theming or Fluent v9 integration.

## Routing logic

| User intent | Skill to invoke |
|---|---|
| "Scaffold a new Code App" | Official `code-apps-preview:create-code-app`, then `ppbp-codeapps-setup` |
| "Add a connector" | Official `code-apps-preview:add-connector`, then `ppbp-codeapps-connectors` |
| "Style the app / Fluent theming" | `ppbp-codeapps-uxui` |
| "Deploy the Code App" | Official `code-apps-preview:deploy` |
| "General Code App conventions" | `ppbp-codeapps-overview` |

## Constraints

The paired official skill is `code-apps-preview`. Verify it is active before invoking any skill in this plugin. This plugin does not cover scaffolding commands, connector syntax, or deployment flags — those are owned by the official skill. All ppbp-codeapps skills are additive conventions only.
