---
name: ppbp-overview
description: >
  Power Platform project orientation — canonical repository layout and skill routing.
  Use when the user asks how the project is structured, which skill handles a task,
  or where a file belongs in the repo.
  Load this skill whenever the active project is a Power Platform repository.
license: MIT
metadata:
  author: powerplatform-bestpractices
  version: "2.2.0"
---

## Official skill

No official Microsoft skill exists for this topic. This skill covers project-level orientation only.

## Purpose

This skill is declared in the project's agent instruction file (`CLAUDE.md` for Claude Code, `.github/copilot-instructions.md` for GitHub Copilot), which causes it to load automatically at the start of every session in a Power Platform repository. It does not drive any action on its own — it orients the agent on the canonical repository layout and routes requests to the right skill.

**Do not create folders or files proactively.** Each folder is created by the skill responsible for it, when the first piece of work in that domain is requested.

## Canonical repository layout

```
<repo-root>/
├── CLAUDE.md                          # Agent instructions for Claude Code
├── .github/
│   └── copilot-instructions.md        # Agent instructions for GitHub Copilot
├── README.md                          # Human-facing project overview
│
├── data/
│   ├── model/           # Dataverse data-model specifications
│   ├── scripts/         # Python scripts that create tables, columns, and choices
│   └── import/          # Python scripts that load records into Dataverse
│       ├── prereq/      # Reference/lookup data — runs first; idempotent
│       ├── prod/        # Production initial data
│       ├── dev/         # Dev/test seed data — never runs in prod
│       ├── temp/        # One-off scripts — deleted after execution
│       └── RUNLOG.md    # Execution log
│
├── codeapps/
│   └── <app-name>/      # One subfolder per Code App (independent Vite project)
│
├── plugins/
│   └── <plugin-name>/   # One subfolder per Dataverse Plugin project
│
└── genpages/
    └── <model-app-name>/
        └── <page-name>/ # One subfolder per Generative Page
```

## Folder → skill routing

| Folder | Relevant skill |
|---|---|
| `data/model/`, `data/scripts/` | `dataverse:dv-metadata`, `ppbp-dv-metadata-overview`, `ppbp-dv-tables`, `ppbp-dv-columns`, `ppbp-dv-global-choices` |
| `data/import/` | `dataverse:dv-data`, `ppbp-dv-data-overview`, `ppbp-dv-data-scripts`, `ppbp-dv-data-import` |
| `codeapps/<app>/` | `code-apps-preview:create-code-app`, `ppbp-codeapps-overview`, `ppbp-codeapps-setup`, `ppbp-codeapps-connectors` |
| `plugins/<plugin>/` | `ppbp-dv-plugins-overview`, `ppbp-dv-step-plugin`, `ppbp-dv-custom-api`, `ppbp-dv-plugin-build` |
| `genpages/<app>/<page>/` | `model-apps:genpage`, `ppbp-genpages-overview` |
| New project setup | `ppbp-init` |
| README.md maintenance | `ppbp-readme` |

## Anti-patterns (DO NOT DO)

| Anti-pattern | Correct approach |
|---|---|
| Creating `plugins/`, `codeapps/`, or `genpages/` folders before the first piece of work in that domain | Create folders on demand, when the relevant skill scaffolds the first asset |
| Putting Python scripts directly at repo root | Place them in `data/scripts/` or `data/import/` |
| Multiple Code App source files mixed in a single `codeapps/` folder | One subfolder per app — each is an independent Vite project |
| Naming pages at repo root without an intermediate model-app folder | Always use `genpages/<model-app>/<page>` |

## Skill boundaries

This skill covers project layout and skill routing only. It does not cover:

- Creating a new project, agent instruction files → `ppbp-init`
- README.md content and maintenance → `ppbp-readme`
- Dataverse table and column naming → `ppbp-dv-tables`, `ppbp-dv-columns`
- Code App development → `ppbp-codeapps-overview`, `ppbp-codeapps-setup`, `ppbp-codeapps-connectors`
- Plugin development → `ppbp-dv-plugins-overview`
- Generative Pages → `ppbp-genpages-overview`
- Solution lifecycle → `ppbp-alm-solutions`, `ppbp-alm-pipelines`
- Dataverse data manipulation → `ppbp-dv-data-overview`
