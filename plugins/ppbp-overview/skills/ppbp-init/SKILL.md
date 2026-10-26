---
name: ppbp-init
description: >
  Power Platform new project initialisation. Use when the user is starting a new Power
  Platform project from scratch — creating the agent instruction file (a single
  AGENTS.md shared by Claude Code and GitHub Copilot), writing the initial README.md
  skeleton and the .env.dev / .env.uat / .env.prod environment descriptors, or setting
  up the project for the first time. Also use when the user asks
  "how do I set up Claude Code / Copilot for this project" or "what files do I need to
  create to start a Power Platform repo".
license: MIT
user-invocable: true
model: sonnet
allowed-tools: Read, Write, Edit, Bash, Grep, Glob, WebSearch
argument-hint: "<project-name>"
metadata:
  author: powerplatform-bestpractices
  version: "1.5.0"
---

## Official skill

No official Microsoft skill exists for this topic. This skill covers new project initialisation conventions only.

## Initialisation checklist

When starting a new Power Platform project, create these files and nothing else:

1. **Agent instruction file** — `AGENTS.md` at the repo root
2. **README.md skeleton** — see `ppbp-readme` for the full required content spec
3. **Environment descriptors** — `.env.dev`, `.env.uat`, `.env.prod` at the repo root
4. **`.gitignore` entries** — local secrets and tool output

Do **not** create `dataverse/`, `data/`, `codeapps/`, `plugins/`, `genpages/`, `uxui/`, `solutions/` or pipeline folders at this stage — each domain folder is created by the skill responsible for it when the first piece of work in that domain is requested.

## Agent instruction file

Write a single `AGENTS.md` at the repo root, whichever agent is active. Claude Code and GitHub Copilot both read it, so one file keeps the instructions identical for everyone on the team. Do not also create `CLAUDE.md` or `.github/copilot-instructions.md`.

The agent instruction file tells agents **how to work in this project**, not what the project is. Keep it short; all project context belongs in `README.md`.

Required content:

```markdown
# <Project Name> — Agent Instructions

Project context: see [README.md](./README.md).

## Active skills

<!-- List only the skills relevant to this project. Each DOMAIN ppbp-* skill requires
     its paired official Microsoft skill to be installed — both must appear here. The
     meta skills (overview/init/readme) have no official counterpart. -->

- `ppbp-overview` — project layout and skill routing
- `ppbp-init` — new project setup
- `ppbp-readme` — README maintenance
- `dataverse:dv-solution` + `ppbp-alm-overview` + `ppbp-alm-solutions` + `ppbp-alm-pipelines` — ALM / solution lifecycle
- `dataverse:dv-metadata` + `ppbp-dv-metadata-overview` + `ppbp-dv-tables` + `ppbp-dv-columns` + `ppbp-dv-global-choices` + `ppbp-dv-metadata-review` — Dataverse schema
- `dataverse:dv-data` + `ppbp-dv-data-overview` + `ppbp-dv-data-scripts` + `ppbp-dv-data-import` — Dataverse data
- `code-apps-preview:create-code-app` + `ppbp-codeapps-overview` + `ppbp-codeapps-setup` + `ppbp-codeapps-react` + `ppbp-codeapps-connectors` + `ppbp-codeapps-uxui` — Code Apps
- `dataverse:dv-overview` + `ppbp-dv-plugins-overview` + `ppbp-dv-step-plugin` + `ppbp-dv-custom-api` + `ppbp-dv-plugin-build` — Dataverse plug-ins
- `model-apps:genpage` + `ppbp-genpages-overview` + `ppbp-genpages-uxui` — Generative Pages

## Conventions

<!-- Project-specific rules that override or supplement the best-practice skills. -->

## Out of scope

<!-- What this repository does NOT manage. -->
```

Remove skills from the list that are not relevant to this specific project.

Do **not** put environment URLs, solution names, publisher prefix, or architecture diagrams in the agent instruction file. Environment URLs belong in `.env.<stage>`, and everything else in `README.md`.

## Environment descriptors

Each environment is described once, at the repo root, in a file named after its stage. These files are the **single place** that holds environment URLs and tenant IDs. They contain **no secrets** and are committed.

```dotenv
# .env.dev — environment descriptor (committed, NO secrets)
ENVIRONMENT_STAGE=dev
DATAVERSE_URL=https://<org>-dev.crm4.dynamics.com
TENANT_ID=<tenant-guid>
```

Create `.env.uat` and `.env.prod` the same way, with `ENVIRONMENT_STAGE=uat` / `prod`. Ask the user for the URLs and the tenant ID. Never guess them.

- `ENVIRONMENT_STAGE` is the guard key. Any tool that changes the schema or the plug-in registrations must target `.env.dev` only, and refuse to run unless the stage is `dev` and the URL differs from UAT and prod.
- Authentication is the developer's own `az login` session, so these files never need secrets.

Add to `.gitignore`, keeping the descriptors tracked:

```gitignore
# Local secrets and tool caches (e.g. the .env written by dataverse:dv-connect)
.env
.venv/
```

Also add the cache or plan directories that the project's own tools document.

## README.md skeleton

At initialisation, create a `README.md` with the section headings and placeholder content. The full content spec for each section is in `ppbp-readme`.

```markdown
# <Project Name>

## Project overview

<!-- One paragraph: name, functional description, business context. -->

## Environments

| Environment | Descriptor | Purpose |
|---|---|---|
| Dev | [`.env.dev`](./.env.dev) | Active development |
| UAT | [`.env.uat`](./.env.uat) | QA / user acceptance |
| Prod | [`.env.prod`](./.env.prod) | Production |

## Publisher and project code

- **Publisher prefix:** `prfx_`
- **Project code:** `<code>`
- **Shared environment:** Yes / No

## Power Platform solutions

<!-- Functional name, unique name, one-sentence purpose. Mermaid dependency diagram. -->

## Global architecture

<!-- Mermaid diagram: tables, apps, flows, external systems, plugins. -->

## Prerequisites

- `pac` CLI ≥ ...
- Python ≥ 3.10
- Azure CLI (`az login`) — authentication for Python tooling against Dataverse
- Node ≥ 18

## Getting started

```sh
# Commands a new developer runs after cloning
```

## Repository map

<!-- One line per top-level folder. -->
```

## Anti-patterns (DO NOT DO)

| Anti-pattern | Correct approach |
|---|---|
| Writing `CLAUDE.md` or `.github/copilot-instructions.md`, or one per agent | A single root `AGENTS.md` — two instruction files drift apart |
| Leaving the instruction file empty or with only comments | Fill in the active skills list before running any other skill — agents need it to route correctly |
| Putting environment URLs or solution names in the agent instruction file | URLs belong in `.env.<stage>`, solutions in `README.md`; the instruction file references them |
| Secrets (client secrets, tokens, passwords) in `.env.dev` / `.env.uat` / `.env.prod` | Descriptors only; authenticate with `az login`; keep secrets in the gitignored `.env` or a vault |
| Environment URLs repeated in README, scripts or pipelines | Read them from `.env.<stage>`; the README points to the descriptor |
| Creating domain folders (`dataverse/`, `data/`, `codeapps/`, `uxui/`, etc.) at project initialisation | Create folders on demand, when the relevant skill scaffolds the first asset |
| Skipping the README.md skeleton | Create the skeleton immediately — agents read `README.md` for context before every task |

## Skill boundaries

This skill covers new project initialisation only. It does not cover:

- Ongoing README maintenance and content spec → `ppbp-readme`
- Project layout and skill routing → `ppbp-overview`
- Dataverse schema design → `ppbp-dv-tables`, `ppbp-dv-columns`
- Solution lifecycle → `ppbp-alm-solutions`
