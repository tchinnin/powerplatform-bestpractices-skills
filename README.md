# powerplatform-bestpractices

A plugin marketplace of best-practice skills for Claude Code and GitHub Copilot, covering Power Platform development — Dataverse schema, plug-ins, ALM, Code Apps, and Generative Pages.

## What this is

Microsoft publishes **official skills** that document the canonical way to use Power Platform APIs and tools. This marketplace provides **best-practice skills** (`ppbp-*`) that sit on top — adding opinionated conventions, team patterns, and hard-won implementation guidance. They are additive: they never replace official skills, they extend them.

## Plugins

| Plugin | Domain |
|---|---|
| `ppbp-overview` | Project orientation: repository layout, skill routing, project initialisation, README maintenance |
| `ppbp-alm` | Solution design, naming, versioning, segmentation, deployment pipelines |
| `ppbp-codeapps` | Power Apps Code Apps: repository structure, React conventions, connectors, UX/UI |
| `ppbp-dataverse-metadata` | Dataverse schema design: table, column and global Choice conventions, model review, dev-only change principles |
| `ppbp-dataverse-data` | Dataverse data scripts, initial imports, bulk operations |
| `ppbp-dataverse-plugins` | Dataverse plug-ins: project scaffolding and build, step and Custom API design, dev-only registration principles |
| `ppbp-generativepages` | Generative Pages for model-driven apps |

Each plugin has one `*-overview` skill, which is the entry point for its domain. That skill's `## Domain scope` table lists the plugin's other skills.

## Installation

Claude Code:

```sh
/plugin marketplace add tchinnin/powerplatform-bestpractices-skills
/plugin install ppbp-overview@powerplatform-bestpractices
```

GitHub Copilot CLI:

```sh
copilot plugin marketplace add tchinnin/powerplatform-bestpractices-skills
copilot plugin install ppbp-overview@powerplatform-bestpractices
```

Install the matching official Microsoft plugins as well (for example `dataverse`, `code-apps`). The `ppbp-*` skills build on them.

## Recommended companion

These skills define conventions, not tooling: apply them with whatever tool you use to change Dataverse. If you want the schema and the plug-in registrations managed **as code** (declarative YAML, plan → confirm → apply to the dev environment), one option is the [`dataverse-as-code`](https://github.com/tchinnin/dataverse-as-code) marketplace. Both work independently of each other.

```sh
/plugin marketplace add tchinnin/dataverse-as-code
/plugin install dataverse-metadata-as-code@dataverse-as-code
/plugin install dataverse-plugins-as-code@dataverse-as-code
```

## Repository map

```
.
├── AGENTS.md                      # Authoring and consistency rules (read by every agent)
├── .claude-plugin/
│   └── marketplace.json           # Marketplace registry (Claude Code + Copilot)
└── plugins/
    └── ppbp-<domain>/
        ├── .claude-plugin/plugin.json
        ├── agents/ hooks/                 # optional — only for domains that need deterministic tooling
        └── skills/ppbp-<skill>/SKILL.md (+ references/, scripts/, tests/)
```

Authoring standards, naming conventions, token budgets, versioning rules, and commit conventions are in [AGENTS.md](./AGENTS.md).
