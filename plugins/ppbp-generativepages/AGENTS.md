# ppbp-generativepages — Agent Orchestration

## Purpose

This plugin covers Power Apps Generative Pages best practices: repository organisation under `genpages/<model-app>/<page>/`, Fluent v9 theming conventions, and team conventions layered on top of the official `model-apps:genpage` skill. The Fluent theming reference in `ppbp-genpages-uxui/references/fluent-theming.md` contains the full theming guidance.

## Skill load order

Load `ppbp-genpages-overview` first to establish the folder layout and the boundary between what the official skill owns and what these best-practice skills add. Then load `ppbp-genpages-uxui` when working on theming or Fluent v9 integration.

## Routing logic

| User intent | Skill to invoke |
|---|---|
| "Create a generative page" / "scaffold a page" | Official `model-apps:genpage`, then `ppbp-genpages-overview` |
| "Theme the page" / "Fluent v9 styling" | `ppbp-genpages-uxui` |
| "How should pages be organised in the repo?" | `ppbp-genpages-overview` |

## Constraints

The paired official skill is `model-apps:genpage`. Verify it is active before invoking any skill in this plugin. The official skill owns all scaffolding, Dataverse entity detection, and TypeScript/React generation — the ppbp-generativepages skills add only team-specific conventions the official skill does not cover. Load `ppbp-genpages-uxui/references/fluent-theming.md` before writing any Fluent v9 theming code.
