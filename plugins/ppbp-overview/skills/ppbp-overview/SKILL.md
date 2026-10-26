---
name: ppbp-overview
description: >
  Power Platform project orientation — canonical repository layout and skill routing.
  Use when the user asks how the project is structured, which skill handles a task,
  or where a file belongs in the repo.
  Load this skill whenever the active project is a Power Platform repository.
license: MIT
user-invocable: true
model: sonnet
allowed-tools: Read, Bash, Grep, Glob, WebSearch
metadata:
  author: powerplatform-bestpractices
  version: "2.6.0"
---

## Official skill

No official Microsoft skill exists for this topic. This skill covers project-level orientation only.

## Purpose

This skill is declared in the project's agent instruction file (`AGENTS.md` at the repo root, read by both Claude Code and GitHub Copilot), which causes it to load automatically at the start of every session in a Power Platform repository. It does not drive any action on its own — it orients the agent on the canonical repository layout and routes requests to the right skill.

**Do not create folders or files proactively.** Each folder is created by the skill responsible for it, when the first piece of work in that domain is requested.

## Canonical repository layout

```
<repo-root>/
├── AGENTS.md                          # Agent instructions (Claude Code + GitHub Copilot)
├── README.md                          # Human-facing project overview
├── .env.dev / .env.uat / .env.prod    # Environment descriptors (URL, tenant, stage) — committed, no secrets
├── .gitignore                         # Ignores .env (local secrets), .venv/, tool caches
│
├── dataverse/
│   └── model/           # Data-model review docs — Mermaid ERD + table specs (agents + humans)
│
├── data/
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
├── genpages/
│   └── <model-app-name>/
│       └── <page-name>/ # One subfolder per Generative Page
│
├── uxui/                # Shared design system for Code Apps and Generative Pages
│   ├── guidelines.md    # Colours, typography, spacing — one spec for the whole repo
│   ├── assets/          # Shared logo, icons, fonts
│   ├── codeapps/<app-name>/                   # HTML previews — mirrors codeapps/<app-name>
│   └── genpages/<model-app-name>/<page-name>/ # HTML previews — mirrors genpages/<model-app-name>/<page-name>
│
├── solutions/
│   └── <solution-unique-name>/  # Unpacked solution source — only if the project version-controls it
├── .github/workflows/   # GitHub Actions pipelines
└── pipelines/           # Azure DevOps pipelines (one CI system per project)
```

If the project defines its schema or plug-in registrations as code, the tool's files live under `dataverse/` (schema) or in the plug-in project folder (registrations), in that tool's own format. This layout doesn't prescribe a tool.

## Folder → skill routing

| Folder | Relevant skill |
|---|---|
| `dataverse/` | `dataverse:dv-metadata`, `ppbp-dv-metadata-overview`, `ppbp-dv-tables`, `ppbp-dv-columns`, `ppbp-dv-global-choices`, `ppbp-dv-metadata-review` |
| `.env.dev`, `.env.uat`, `.env.prod` | `ppbp-init` |
| `data/import/` | `dataverse:dv-data`, `ppbp-dv-data-overview`, `ppbp-dv-data-scripts`, `ppbp-dv-data-import` |
| `codeapps/<app>/` | `code-apps-preview:create-code-app`, `ppbp-codeapps-overview`, `ppbp-codeapps-setup`, `ppbp-codeapps-react`, `ppbp-codeapps-connectors`, `ppbp-codeapps-uxui` |
| `plugins/<plugin>/` | `dataverse:dv-overview`, `ppbp-dv-plugins-overview`, `ppbp-dv-step-plugin`, `ppbp-dv-custom-api`, `ppbp-dv-plugin-build` |
| `genpages/<app>/<page>/` | `model-apps:genpage`, `ppbp-genpages-overview`, `ppbp-genpages-uxui` |
| `uxui/` | `ppbp-codeapps-uxui` (owns `guidelines.md` and `uxui/codeapps/`), `ppbp-genpages-uxui` (`uxui/genpages/`) |
| `solutions/`, `.github/workflows/`, `pipelines/` | `dataverse:dv-solution`, `ppbp-alm-overview`, `ppbp-alm-solutions`, `ppbp-alm-pipelines` |
| New project setup | `ppbp-init` |
| README.md maintenance | `ppbp-readme` |

## Anti-patterns (DO NOT DO)

| Anti-pattern | Correct approach |
|---|---|
| Creating `dataverse/`, `data/`, `codeapps/`, `plugins/`, `genpages/`, `uxui/`, `solutions/` or pipeline folders before the first piece of work in that domain | Create folders on demand, when the relevant skill scaffolds the first asset |
| Putting Python scripts directly at repo root | Data scripts go in `data/import/`; schema changes are never made from data scripts |
| Environment URLs scattered across scripts, pipelines or docs | One descriptor per environment at the root: `.env.dev`, `.env.uat`, `.env.prod` |
| Multiple Code App source files mixed in a single `codeapps/` folder | One subfolder per app — each is an independent Vite project |
| Naming pages at repo root without an intermediate model-app folder | Always use `genpages/<model-app>/<page>` |
| Design previews whose path does not mirror the source path | `uxui/codeapps/<app-name>/` and `uxui/genpages/<model-app-name>/<page-name>/` |
| Data-model docs or metadata under `data/` | Schema docs and definitions live under `dataverse/`; `data/` holds record imports only |

## Skill boundaries

This skill covers project layout and skill routing only. It does not cover:

- Creating a new project, agent instruction files → `ppbp-init`
- README.md content and maintenance → `ppbp-readme`
- Dataverse schema design and naming → `ppbp-dv-metadata-overview`
- Code App development → `ppbp-codeapps-overview`, `ppbp-codeapps-setup`, `ppbp-codeapps-react`, `ppbp-codeapps-connectors`, `ppbp-codeapps-uxui`
- Plugin development and registration → `ppbp-dv-plugins-overview`
- Generative Pages → `ppbp-genpages-overview`, `ppbp-genpages-uxui`
- Solution lifecycle and pipelines → `ppbp-alm-overview`, `ppbp-alm-solutions`, `ppbp-alm-pipelines`
- Dataverse data manipulation → `ppbp-dv-data-overview`
