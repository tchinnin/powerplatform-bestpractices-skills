---
name: ppbp-init
description: >
  Power Platform new project initialisation. Use when the user is starting a new Power
  Platform project from scratch — creating the agent instruction file (CLAUDE.md for
  Claude Code, .github/copilot-instructions.md for GitHub Copilot), writing the initial
  README.md skeleton, or setting up the project for the first time. Also use when the
  user asks "how do I set up Claude Code for this project" or "what files do I need to
  create to start a Power Platform repo".
license: MIT
metadata:
  author: powerplatform-bestpractices
  version: "1.1.0"
---

## Official skill

No official Microsoft skill exists for this topic. This skill covers new project initialisation conventions only.

## Initialisation checklist

When starting a new Power Platform project, create these two files and nothing else:

1. **Agent instruction file** — `CLAUDE.md` (Claude Code) or `.github/copilot-instructions.md` (GitHub Copilot)
2. **README.md skeleton** — see `ppbp-readme` for the full required content spec

Do **not** create `data/`, `codeapps/`, `plugins/`, or `genpages/` folders at this stage — each domain folder is created by the skill responsible for it when the first piece of work in that domain is requested.

## Agent instruction file

**Write the correct file based on the active agent:**

| Agent | File |
|---|---|
| Claude Code | `CLAUDE.md` (repo root) |
| GitHub Copilot | `.github/copilot-instructions.md` |

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
- `dataverse:dv-metadata` + `ppbp-dv-metadata-overview` + `ppbp-dv-tables` + `ppbp-dv-columns` + `ppbp-dv-global-choices` — Dataverse schema
- `dataverse:dv-data` + `ppbp-dv-data-overview` + `ppbp-dv-data-scripts` + `ppbp-dv-data-import` — Dataverse data
- `code-apps-preview:create-code-app` + `ppbp-codeapps-overview` + `ppbp-codeapps-setup` + `ppbp-codeapps-connectors` — Code Apps
- `ppbp-dv-plugins-overview` + `ppbp-dv-step-plugin` + `ppbp-dv-custom-api` + `ppbp-dv-plugin-build` — Dataverse plug-ins
- `model-apps:genpage` + `ppbp-genpages-overview` — Generative Pages

## Conventions

<!-- Project-specific rules that override or supplement the best-practice skills. -->

## Out of scope

<!-- What this repository does NOT manage. -->
```

Remove skills from the list that are not relevant to this specific project.

Do **not** put environment URLs, solution names, publisher prefix, or architecture diagrams in the agent instruction file — those belong in `README.md`.

## README.md skeleton

At initialisation, create a `README.md` with the section headings and placeholder content. The full content spec for each section is in `ppbp-readme`.

```markdown
# <Project Name>

## Project overview

<!-- One paragraph: name, functional description, business context. -->

## Environments

| Environment | URL | Purpose |
|---|---|---|
| Dev | `https://<org>.crm.dynamics.com` | Active development |
| Test | `https://<org>.crm.dynamics.com` | QA / UAT |
| Prod | `https://<org>.crm.dynamics.com` | Production |

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
| Writing `CLAUDE.md` when the agent is GitHub Copilot, or `.github/copilot-instructions.md` when the agent is Claude Code | Use the file that matches the active agent |
| Leaving the instruction file empty or with only comments | Fill in the active skills list before running any other skill — agents need it to route correctly |
| Putting environment URLs or solution names in the agent instruction file | Those belong in `README.md`; the instruction file references `README.md` |
| Creating domain folders (`data/`, `codeapps/`, etc.) at project initialisation | Create folders on demand, when the relevant skill scaffolds the first asset |
| Skipping the README.md skeleton | Create the skeleton immediately — agents read `README.md` for context before every task |

## Skill boundaries

This skill covers new project initialisation only. It does not cover:

- Ongoing README maintenance and content spec → `ppbp-readme`
- Project layout and skill routing → `ppbp-overview`
- Dataverse schema design → `ppbp-dv-tables`, `ppbp-dv-columns`
- Solution lifecycle → `ppbp-alm-solutions`
