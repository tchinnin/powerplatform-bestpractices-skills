---
name: ppbp-overview
description: >
  Power Platform project orientation — canonical repository layout and skill routing.
  Use when the user asks how the project is structured, which skill handles a task,
  where a file belongs in the repo, or wants to set up CLAUDE.md /
  .github/copilot-instructions.md for a new Power Platform project.
  Load this skill whenever the active project is a Power Platform repository.
license: MIT
metadata:
  author: powerplatform-bestpractices
  version: "0.1.0"
---

## Official skill

No official Microsoft skill exists for this topic. This skill covers project-level conventions only.

## Purpose

This skill is declared in the project's agent instruction file (`CLAUDE.md` for Claude Code, `.github/copilot-instructions.md` for GitHub Copilot), which causes it to load automatically at the start of every session in a Power Platform repository. It does not drive any action on its own — it orients the agent on the canonical repository layout and routes requests to the right skill.

**Do not create folders or files proactively.** Each folder is created by the skill responsible for it, when the first piece of work in that domain is requested. For example, `plugins/` is created by `ppbp-dv-plugins` when the first plugin is scaffolded, not at project setup.

## Canonical repository layout

This is the target layout for a fully built-out project. At any point in time, only the folders relevant to work already done will exist.

```
<repo-root>/
├── CLAUDE.md                          # Agent instructions for Claude Code
├── .github/
│   └── copilot-instructions.md        # Agent instructions for GitHub Copilot
├── README.md                          # Human-facing project overview
│
├── data/
│   ├── model/           # Dataverse data-model specifications
│   │   └── *.md         # One file per table group or domain (ERD in Mermaid, full column spec)
│   ├── scripts/         # Python scripts that create tables, columns, and choices
│   │   └── *.py         # Written with dataverse:dv-metadata / ppbp-dv-metadata
│   └── import/          # Python scripts that load records into Dataverse
│       └── *.py         # Real or seed data; written with dataverse:dv-data
│
├── codeapps/
│   └── <app-name>/      # One subfolder per Code App (independent Vite project)
│
├── plugins/
│   └── <plugin-name>/   # One subfolder per Dataverse Plugin project
│
└── genpages/
    └── <model-app-name>/
        └── <page-name>/ # One subfolder per Generative Page inside the model-driven app
```

### Folder → skill routing

| Folder | Created by | Relevant skill |
|---|---|---|
| `data/model/` | `ppbp-dv-metadata` | `ppbp-dv-metadata` |
| `data/scripts/` | `ppbp-dv-metadata` | `dataverse:dv-metadata`, `ppbp-dv-metadata` |
| `data/import/` | first data-import task | `dataverse:dv-data` |
| `codeapps/<app>/` | `ppbp-code-apps` | `code-apps-preview:create-code-app`, `ppbp-code-apps` |
| `plugins/<plugin>/` | `ppbp-dv-plugins` | `ppbp-dv-plugins` |
| `genpages/<app>/<page>/` | `ppbp-generative-pages` | `model-apps:genpage`, `ppbp-generative-pages` |

## README.md

README.md is the **single source of project truth**. All project-specific context lives here; the agent instruction file references it rather than duplicating it.

Required sections, in order:

**1. Project overview** — name, one-paragraph functional description, business context.

**2. Environments**

| Environment | URL | Purpose |
|---|---|---|
| Dev | `https://<org>.crm.dynamics.com` | Active development |
| Test | `https://<org>.crm.dynamics.com` | QA / UAT |
| Prod | `https://<org>.crm.dynamics.com` | Production |

**3. Publisher and project code**
- **Publisher prefix** — the `prfx_` used for all custom Dataverse objects.
- **Project code** — short code appended after the prefix in shared environments: `prfx_<code>_TableName`.
- Shared environment? Yes/No — if yes, state which other projects share the same publisher.

**4. Power Platform solutions** — functional name, unique name, one-sentence purpose, dependency order. Represent the dependency chain as a Mermaid diagram.

> Solution design is governed by `ppbp-alm`. Apply that skill before deciding how to split or name solutions.

**5. Global architecture** — Mermaid diagram covering: Dataverse tables, Power Apps, Power Automate flows, external systems, plugins.

**6. Prerequisites** — required CLI tools and minimum versions: `pac`, `python ≥ 3.10`, `node ≥ 18`.

**7. Getting started** — exact commands a new developer runs after cloning.

**8. Repository map** — one line per top-level folder.

## Agent instruction file

The agent instruction file tells agents **how to work in this project**, not what the project is. Keep it short; reference README.md for all project context.

**Write the correct file based on the active agent:**

| Agent | File |
|---|---|
| Claude Code | `CLAUDE.md` (repo root) |
| GitHub Copilot | `.github/copilot-instructions.md` |

Both files share the same required content — only the path differs.

Required content:

```markdown
# <Project Name> — Agent Instructions

Project context: see [README.md](./README.md).

## Active skills

<!-- List only the skills relevant to this project. Each ppbp-* skill requires its
     paired official Microsoft skill to be installed — both must appear here. -->

- `ppbp-overview` — project layout and skill routing
- `dataverse:dv-solution` + `ppbp-alm` — solution lifecycle
- `dataverse:dv-metadata` + `ppbp-dv-metadata` — Dataverse schema conventions
- `code-apps-preview:create-code-app` + `ppbp-code-apps` — Code App conventions
- `ppbp-dv-plugins` — Dataverse plug-ins and Custom APIs (no official skill)
- `model-apps:genpage` + `ppbp-generative-pages` — Generative Page conventions

## Conventions

<!-- Project-specific rules that override or supplement the best-practice skills. -->

## Out of scope

<!-- What this repository does NOT manage. -->
```

Do **not** put environment URLs, solution names, publisher prefix, or architecture diagrams in the agent instruction file — those belong in README.md.

## Data model files (`data/model/`)

Each `.md` file in `data/model/` must contain:

1. **Domain name and short description** (H1 heading).
2. **Mermaid ERD** — `erDiagram` syntax with all tables, FK relationships, and cardinality.
3. **Table specs** — one section per table: Display Name, Schema Name, Description, full column list, relationship list.
4. **Open questions** — unresolved design decisions, cleared as decisions are made.

## Anti-patterns (DO NOT DO)

| Anti-pattern | Correct approach |
|---|---|
| Creating `plugins/`, `codeapps/`, or `genpages/` folders before the first piece of work in that domain | Create folders on demand, when the relevant skill scaffolds the first asset |
| Putting Python scripts directly at repo root | Place them in `data/scripts/` or `data/import/` |
| One flat `data/` folder with mixed model docs and scripts | Keep `model/`, `scripts/`, `import/` separate |
| Multiple Code App source files mixed in a single `codeapps/` folder | One subfolder per app — each is an independent Vite project with its own `package.json` |
| Putting environment URLs or solution names in the agent instruction file | Those belong in README.md — the instruction file references README.md |
| Skipping README.md or leaving it as a stub | Agents read README.md for environment URLs, publisher prefix, and architecture — an empty README breaks every skill |
| Skipping the agent instruction file or keeping it empty | Fill it in before running any skill — agents need the active skills list and project-specific conventions |
| Writing `CLAUDE.md` when the agent is GitHub Copilot, or `.github/copilot-instructions.md` when the agent is Claude Code | Use the path that matches the active agent |
| Writing schema scripts without a matching model doc | The model doc is the source of truth; always maintain it alongside the script |
| Naming pages at repo root without an intermediate model-app folder | Always use `genpages/<model-app>/<page>` |

## Skill boundaries

This skill covers project layout, skill routing, README structure, and the agent instruction file. It does not cover:

- Dataverse schema design and naming → `ppbp-dv-metadata`
- Writing or deploying schema scripts → `dataverse:dv-metadata`
- Importing data records → `dataverse:dv-data`
- Code App development → `ppbp-code-apps`, `code-apps-preview:create-code-app`
- Plugin development → `ppbp-dv-plugins`
- Generative Pages → `ppbp-generative-pages`, `model-apps:genpage`
- Solution lifecycle and ALM → `ppbp-alm`
