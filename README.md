# powerplatform-bestpractices

A marketplace of best-practice skills for Claude Code and GitHub Copilot, covering Power Platform development — Dataverse schema, plug-ins, ALM, Code Apps, and Generative Pages.

## What this is

Microsoft publishes **official skills** that document the canonical way to use Power Platform APIs and tools. This marketplace provides **best-practice skills** (`ppbp-*`) that sit on top — adding opinionated conventions, team patterns, and hard-won implementation guidance. They are additive: they never replace official skills, they extend them.

## Distribution architecture

```
marketplace: powerplatform-bestpractices
│
├── plugin: ppbp-overview          ← project orientation and setup
│   ├── skill: ppbp-overview       — canonical repo layout + skill routing
│   ├── skill: ppbp-init           — new project setup (agent instruction file + README skeleton)
│   └── skill: ppbp-readme         — ongoing README maintenance
│
├── plugin: ppbp-alm               ← solution lifecycle
│   ├── skill: ppbp-alm-overview   — ALM repo layout + global principles
│   ├── skill: ppbp-alm-solutions  — solution naming, versioning, segmentation
│   └── skill: ppbp-alm-pipelines  — deployment pipeline conventions
│
├── plugin: ppbp-codeapps          ← Code Apps (React + Vite)
│   ├── skill: ppbp-codeapps-overview   — repo layout + global principles
│   ├── skill: ppbp-codeapps-setup      — scaffolding, React 17, deployment
│   └── skill: ppbp-codeapps-connectors — useConnector, type gen, bundle size
│
├── plugin: ppbp-dataverse-metadata  ← Dataverse schema design
│   ├── skill: ppbp-dv-metadata-overview  — repo layout + core naming rule
│   ├── skill: ppbp-dv-tables             — table naming, ownership, primary name column
│   ├── skill: ppbp-dv-columns            — column naming, type suffixes
│   └── skill: ppbp-dv-global-choices     — global Choice naming + solution integration
│
├── plugin: ppbp-dataverse-plugins   ← Dataverse plug-ins and Custom APIs
│   ├── skill: ppbp-dv-plugins-overview  — repo layout + global principles
│   ├── skill: ppbp-dv-plugin-build      — PAC CLI scaffold, build, deployment
│   ├── skill: ppbp-dv-step-plugin       — execution pipeline, images, registration
│   └── skill: ppbp-dv-custom-api        — Custom API design, bound/unbound, parameters
│
└── plugin: ppbp-generativepages     ← Generative Pages (model-driven apps)
    ├── skill: ppbp-genpages-overview    — repo layout + global principles
    ├── skill: ppbp-genpages-setup       — manifest, sitemap, deployment
    └── skill: ppbp-genpages-development — SDK, Fluent UI v9, data access, navigation
```

### Plugin structure

Every domain plugin follows the same pattern:

- **One `*-overview` skill** — loaded first for any task in the domain. Contains the repository layout for that domain, the domain scope table (which skill covers what), and the global principles shared by all skills in the plugin.
- **N task skills** — each covers one specific concern. They contain no repository layout (that's in the overview) and link back to the overview in `## Skill boundaries`.

## Repository map

```
.
├── .claude-plugin/
│   ├── marketplace.json   # Marketplace registry (lists all 6 domain plugins)
│   └── plugin.json        # Monorepo-level descriptor
├── .github/
│   └── plugins/
│       ├── ppbp-overview/
│       │   ├── plugin.json
│       │   └── skills/ppbp-overview/ ppbp-init/ ppbp-readme/
│       ├── ppbp-alm/
│       │   ├── plugin.json
│       │   └── skills/ppbp-alm-overview/ ppbp-alm-solutions/ ppbp-alm-pipelines/
│       ├── ppbp-codeapps/
│       │   ├── plugin.json
│       │   └── skills/ppbp-codeapps-overview/ ppbp-codeapps-setup/ ppbp-codeapps-connectors/
│       ├── ppbp-dataverse-metadata/
│       │   ├── plugin.json
│       │   └── skills/ppbp-dv-metadata-overview/ ppbp-dv-tables/ ppbp-dv-columns/ ppbp-dv-global-choices/
│       ├── ppbp-dataverse-plugins/
│       │   ├── plugin.json
│       │   └── skills/ppbp-dv-plugins-overview/ ppbp-dv-plugin-build/ ppbp-dv-step-plugin/ ppbp-dv-custom-api/
│       └── ppbp-generativepages/
│           ├── plugin.json
│           └── skills/ppbp-genpages-overview/ ppbp-genpages-setup/ ppbp-genpages-development/
└── CLAUDE.md              # Authoring standards for agents working in this repo
```

## Contributing

Authoring standards, naming conventions, token budgets, versioning rules, and commit conventions are in [CLAUDE.md](./CLAUDE.md).
