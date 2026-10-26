---
name: ppbp-readme
description: >
  Power Platform README.md maintenance. Use when the user wants to update README.md
  to reflect the current state of the repo — adding a new table, solution, app, or
  flow; updating the architecture diagram; filling in a missing section; or keeping
  README.md as the single source of project truth. Also use when README.md is stale,
  incomplete, or missing required sections.
license: MIT
user-invocable: true
model: sonnet
allowed-tools: Read, Bash, Grep, Glob, WebSearch
metadata:
  author: powerplatform-bestpractices
  version: "1.1.1"
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

| Environment | Descriptor | Purpose |
|---|---|---|
| Dev | [`.env.dev`](./.env.dev) | Active development — the only environment with unmanaged solutions |
| UAT | [`.env.uat`](./.env.uat) | QA / user acceptance — managed imports only |
| Prod | [`.env.prod`](./.env.prod) | Production — managed imports only |

Environment URLs and tenant IDs live **only** in the root `.env.<stage>` files, which `ppbp-init` creates. The README points to them and describes each environment's purpose; it never repeats the URLs.

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

Required CLI tools and minimum versions: `pac`, `python ≥ 3.10`, Azure CLI (`az login` — authentication for Python tooling against Dataverse), `node ≥ 18`.

### 7. Getting started

Exact commands a new developer runs after cloning.

### 8. Repository map

One line per top-level folder explaining what it contains. Folder names follow the canonical layout in `ppbp-overview`.

## Data model docs (`dataverse/model/`)

Each `.md` file in `dataverse/model/` is a domain-scoped model document for agent and human review. It must contain:

1. **Domain name and short description** (H1 heading).
2. **Mermaid ERD** — `erDiagram` syntax with all tables, FK relationships, and cardinality.
3. **Table specs** — one section per table: Display Name, Schema Name, Description, full column list, relationship list.
4. **Open questions** — unresolved design decisions; clear them as decisions are made.

The model doc is the review view of the schema, whatever its source (the dev environment, or a schema-as-code tool under `dataverse/`). Update it in the same change as the schema.

## When to update README.md

Update `README.md` immediately after:

- Adding, renaming, or removing a Dataverse table → update the architecture diagram and data model section.
- Creating or restructuring a Power Platform solution → update the solutions section and dependency diagram.
- Scaffolding a new Code App, plugin project, or Generative Page → update the repository map.
- Adding an environment or changing its purpose → update the Environments table (URLs change only in `.env.<stage>`).
- Adding a new external integration → update the architecture diagram.

## Anti-patterns (DO NOT DO)

| Anti-pattern | Correct approach |
|---|---|
| Leaving `README.md` as a stub or with only placeholder text | Fill in every required section; agents read it before every task — an empty README breaks routing |
| Writing environment URLs, solution names, or publisher prefix in the agent instruction file | Environment URLs belong in `.env.<stage>`; solutions and publisher in `README.md`; the instruction file only references them |
| Copying environment URLs into the README Environments table | Point to `.env.<stage>` and describe the purpose |
| Changing the schema without updating the `dataverse/model/` doc | Update both in the same change — reviewers read the `.md` |
| Updating `README.md` architecture section only at project start | Keep it current after every schema or app change; a stale architecture diagram misleads agents |
| One flat `dataverse/model/` file for all tables | One file per domain or table group; large monolithic files are hard to navigate and update |

## Skill boundaries

This skill covers README.md content and maintenance only. It does not cover:

- Initial project setup and agent instruction files → `ppbp-init`
- Project layout and skill routing → `ppbp-overview`
- Dataverse schema design → `ppbp-dv-metadata-overview`, `ppbp-dv-tables`
- Solution design → `ppbp-alm-solutions`
