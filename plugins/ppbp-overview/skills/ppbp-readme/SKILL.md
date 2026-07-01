---
name: ppbp-readme
description: >
  Power Platform README.md maintenance. Use when the user wants to update README.md
  to reflect the current state of the repo — adding a new table, solution, app, or
  flow; updating the architecture diagram; filling in a missing section; or keeping
  README.md as the single source of project truth. Also use when README.md is stale,
  incomplete, or missing required sections.
license: MIT
metadata:
  author: powerplatform-bestpractices
  version: "1.0.0"
---

## Official skill

No official Microsoft skill exists for this topic. This skill covers README.md content conventions only.

## README.md as the single source of truth

`README.md` is the **single source of project truth**. All project-specific context lives here; the agent instruction file references it rather than duplicating it.

**Keep `README.md` current.** Update it whenever a domain object changes: a new table is added, a solution is created, an app is scaffolded, a flow is wired. A stale `README.md` breaks every skill that reads it for context.

## Required sections

README.md must contain these sections, in order:

### 1. Project overview

Name, one-paragraph functional description, business context. No technical jargon.

### 2. Environments

| Environment | URL | Purpose |
|---|---|---|
| Dev | `https://<org>.crm.dynamics.com` | Active development |
| Test | `https://<org>.crm.dynamics.com` | QA / UAT |
| Prod | `https://<org>.crm.dynamics.com` | Production |

### 3. Publisher and project code

- **Publisher prefix** — the `prfx_` used for all custom Dataverse objects.
- **Project code** — short code appended after the prefix in shared environments: `prfx_<code>_TableName`.
- **Shared environment?** Yes / No — if yes, state which other projects share the same publisher.

### 4. Power Platform solutions

Functional name, unique name, one-sentence purpose, import dependency order. Represent the dependency chain as a Mermaid diagram.

> Solution design is governed by `ppbp-alm-solutions`. Apply that skill before deciding how to split or name solutions.

### 5. Global architecture

Mermaid diagram covering: Dataverse tables, Power Apps, Power Automate flows, external systems, plugins.

### 6. Prerequisites

Required CLI tools and minimum versions: `pac`, `python ≥ 3.10`, `node ≥ 18`.

### 7. Getting started

Exact commands a new developer runs after cloning.

### 8. Repository map

One line per top-level folder explaining what it contains.

## Data model files (`data/model/`)

Each `.md` file in `data/model/` is a domain-scoped model document. It must contain:

1. **Domain name and short description** (H1 heading).
2. **Mermaid ERD** — `erDiagram` syntax with all tables, FK relationships, and cardinality.
3. **Table specs** — one section per table: Display Name, Schema Name, Description, full column list, relationship list.
4. **Open questions** — unresolved design decisions; clear them as decisions are made.

Always maintain a model doc alongside every schema script in `data/scripts/`. The model doc is the source of truth; the script is derived from it.

## When to update README.md

Update `README.md` immediately after:

- Adding, renaming, or removing a Dataverse table → update the architecture diagram and data model section.
- Creating or restructuring a Power Platform solution → update the solutions section and dependency diagram.
- Scaffolding a new Code App, plugin project, or Generative Page → update the repository map.
- Changing environment URLs → update the Environments table.
- Adding a new external integration → update the architecture diagram.

## Anti-patterns (DO NOT DO)

| Anti-pattern | Correct approach |
|---|---|
| Leaving `README.md` as a stub or with only placeholder text | Fill in every required section; agents read it before every task — an empty README breaks routing |
| Writing environment URLs, solution names, or publisher prefix in the agent instruction file instead of `README.md` | All project context belongs in `README.md`; the instruction file only references it |
| Skipping `data/model/` docs and committing only schema scripts | The model doc is the source of truth; always create or update it before or alongside the script |
| Updating `README.md` architecture section only at project start | Keep it current after every schema or app change; a stale architecture diagram misleads agents |
| One flat `data/model/` file for all tables | One file per domain or table group; large monolithic files are hard to navigate and update |

## Skill boundaries

This skill covers README.md content and maintenance only. It does not cover:

- Initial project setup and agent instruction files → `ppbp-init`
- Project layout and skill routing → `ppbp-overview`
- Dataverse schema scripting → `dataverse:dv-metadata`, `ppbp-dv-tables`
- Solution design → `ppbp-alm-solutions`
