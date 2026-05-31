# CLAUDE.md — Power Platform Best Practices Plugin

## What This Repo Is

A plugin for Claude Code and GitHub Copilot that distributes Power Platform best-practice skills. Skills teach agents the right patterns for Dataverse, ALM, Code Apps, Generative Pages, and Dataverse Plugins — without being tied to a specific SDK or toolchain.

## Official Skills vs Best-Practice Skills

Microsoft publishes **official skills** (e.g. `powerplatform:codeapps`, `powerplatform:dataverse`) that document the canonical, supported way to use Power Platform. These are the authoritative source of truth.

This plugin provides **best-practice skills** (`ppbp-*`) that sit on top of the official skills — adding opinionated guidance, team conventions, and hard-won patterns. Best-practice skills must never contradict official skills. If an official skill and a best-practice skill appear to conflict, the official skill takes precedence and the best-practice skill must be updated.

When authoring or updating a skill, always check the corresponding official skill first. At runtime, every `ppbp-*` skill must verify the official skill is active in the agent's context. If it is not installed or enabled, the agent must strongly recommend the user install it before proceeding — the best-practice guidance in this plugin is additive and assumes the official skill is the foundation.

## Skill Authoring Standards

### Language

All content is in English — skill bodies, references, code examples, comments, commit messages.

### Naming

Skill directories and `name` fields follow `ppbp-<concept>` (lowercase, hyphens only). Dataverse-specific skills use the `dv-` infix: `ppbp-dv-<concept>`. The directory name must match `name` exactly.

### Frontmatter

```yaml
---
name: ppbp-<concept>
description: >
  One descriptive sentence plus an inline "Use when the user…" clause naming
  user-intent triggers. Cap at 1,024 characters.
license: MIT
metadata:
  author: powerplatform-bestpractices
  version: "1.0"
---
```

### Token budgets

| Level | Location | Limit |
|---|---|---|
| 1 — Frontmatter | `description` field | ≤200 tokens (~100 target) |
| 2 — Body | Skill body (SKILL.md) | ≤5,000 tokens |
| 3 — References | `references/` files | Unlimited |

### Body structure

Each skill organises its body around the sections that best fit its domain — there is no fixed section order. Domain-specific sections (e.g. `## Naming conventions`, `## Authentication patterns`, `## Deployment`) are encouraged when the topic warrants it.

Two sections are **required on every skill except overviews**:

- `## Official skill` — state which official Microsoft skill this best-practice skill extends (e.g. `powerplatform:codeapps`), with a one-line summary of what it covers. If no official skill exists for this topic, explicitly state: *"No official Microsoft skill exists for this topic."* Agents must load the official skill before this one when one is available. Every `ppbp-*` skill must check at runtime whether the corresponding official skill is active; if it is not, the agent must strongly recommend the user install it before proceeding.
- `## Anti-patterns (DO NOT DO)` — use **Wrong/Correct mapping tables** to make forbidden patterns unambiguous for agents. Format: **Anti-pattern** — description — *correct approach*.
- `## Skill boundaries` — list what this skill does NOT cover and name the skill to use instead. This prevents agents from applying the wrong skill to an adjacent topic.

### Code examples

Code blocks must be complete and executable — no comment-only stubs or placeholder snippets. Language depends on the domain:

| Domain | Expected languages |
|---|---|
| ALM / environment ops | PAC CLI, YAML pipeline |
| Code Apps | TypeScript / React |
| Dataverse Plugins | C# |
| Power Fx | Power Fx |

Large or detailed examples go in `references/`, linked from the body. Reference content must illustrate a pattern, not a specific project implementation.

### Safety and quality controls

For guidance on destructive or irreversible operations (e.g. solution deletion, column removal, environment reset), include a prominent warning block at the top of the relevant section. Skills covering CLI-heavy domains must include Wrong/Correct tables to reduce flag hallucination.

## Skill Scope and Deduplication

Before creating a new skill, verify no existing skill already covers the domain. A new skill must represent a distinct, non-overlapping concern. When in doubt, extend an existing skill rather than creating a near-duplicate. Use the `## Skill boundaries` section of existing skills as the authoritative guide.

## Version Management

When modifying a skill, update `metadata.version` in the skill's frontmatter. When modifying the plugin manifest, bump `version` in `.claude-plugin/plugin.json`.

**Semantic versioning rules:**

- **MAJOR** — skill removal, breaking rename, required section changes, routing changes that break existing agent behavior.
- **MINOR** — new skill, new required section, expanded coverage, new metadata field.
- **PATCH** — typo fixes, clarifications, non-breaking rewording, reference additions.

## Commit Conventions

Use prefixes: `feat:`, `fix:`, `refactor:`, `add:`, or `docs:` (no scopes).
