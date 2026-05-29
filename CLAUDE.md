# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

**powerplatform-bestpractices** is a multi-platform AI plugin that distributes Microsoft Power Platform best-practice skills. It follows the same architecture as `microsoft/dataverse-skills` and `microsoft/power-platform-skills`.

It targets both Claude Code and GitHub Copilot CLI simultaneously via the **SKILL.md standard** ([agentskills.io](https://agentskills.io/specification)) — a single skill definition works across both tools with no separate generation step.

### Domain coverage (one Claude Code skill per domain)

| Skill | Coverage |
|---|---|
| `ppbp-dv-metadata` | Schema design, relationships, column types, naming conventions |
| `ppbp-alm` | Solution layering, environment strategy, deployment pipelines |
| `ppbp-code-apps` | Power Apps Code Apps (React/Vite), connectors |
| `ppbp-generative-pages` | Generative Pages in model-driven apps (React + Fluent UI v9) |
| `ppbp-dv-plugins` | Plug-in steps, Custom APIs, IPlugin pattern |

## Repository structure

```
.
├── .claude-plugin/
│   └── plugin.json             # Plugin manifest (Claude Code + Copilot CLI)
├── skills/
│   ├── ppbp-dv-metadata/
│   │   ├── SKILL.md
│   │   └── references/         # Optional supplementary docs
│   ├── ppbp-alm/
│   ├── ppbp-code-apps/
│   ├── ppbp-generative-pages/
│   └── ppbp-dv-plugins/
└── CLAUDE.md
```

The `.github/plugins/` nesting used in Microsoft's multi-purpose repos is intentionally omitted here — this is a dedicated plugin repo, so skills live directly under `skills/` at the root.

## SKILL.md format

Every skill file must follow this structure exactly:

```markdown
---
name: ppbp-<domain>
description: >
  One-paragraph description of what the skill does AND when to invoke it.
  Max 1024 chars. Used by the AI to decide whether to activate the skill.
license: MIT
metadata:
  author: powerplatform-bestpractices
  version: "1.0"
---

# Markdown body (recommended < 500 lines, < 5000 tokens)
```

**Rules:**
- `name` must match the parent directory name exactly (lowercase, hyphens only).
- `description` is the routing signal — write it as "Use when the user…" to help the AI decide when to activate the skill.
- Body sections: `## Best practices` (numbered list, one rule per line with a short rationale) and `## Common pitfalls` (format: **Pitfall** — description — *mitigation*).
- Link to `references/` files for supplementary content rather than embedding large blocks inline.

## plugin.json manifest

```json
{
  "name": "powerplatform-bestpractices",
  "version": "1.0.0",
  "description": "Power Platform best-practice skills for Dataverse, ALM, security, Code Apps, Generative Pages, Dataverse Plugins, and Power Pages.",
  "author": {
    "name": "Théophile Chin-nin",
    "url": "https://github.com/tchinnin"
  },
  "homepage": "https://github.com/tchinnin/powerplatform-bestpractices-skills",
  "repository": "https://github.com/tchinnin/powerplatform-bestpractices-skills",
  "license": "MIT",
  "keywords": ["power-platform", "dataverse", "alm", "power-apps", "power-pages"]
}
```

## When to activate each skill

A Claude Code instance (or Copilot) should activate a skill when the user:

- Designs or reviews tables/columns/relationships → `ppbp-dv-metadata`
- Discusses solutions, environments, pipelines, managed/unmanaged → `ppbp-alm`
- Builds or modifies a Code App (React/Vite canvas app) → `ppbp-code-apps`
- Works on a Generative Page in a model-driven app → `ppbp-generative-pages`
- Writes or registers a plug-in step or Custom API → `ppbp-dv-plugins`
