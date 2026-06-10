# CLAUDE.md — Power Platform Best Practices Plugin

## What This Repo Is

A plugin for Claude Code and GitHub Copilot that distributes Power Platform best-practice skills. Skills teach agents the right patterns for Dataverse, ALM, Code Apps, Generative Pages, and Dataverse Plugins — without being tied to a specific SDK or toolchain.

## Official Skills vs Best-Practice Skills

Microsoft publishes **official skills** (e.g. `powerplatform:codeapps`, `powerplatform:dataverse`) that document the canonical, supported way to use Power Platform. These are the authoritative source of truth.

This plugin provides **best-practice skills** (`ppbp-*`) that sit on top of the official skills — adding opinionated guidance, team conventions, and hard-won patterns. Best-practice skills must never contradict official skills. If an official skill and a best-practice skill appear to conflict, the official skill takes precedence and the best-practice skill must be updated.

When authoring or updating a skill, always check the corresponding official skill first. At runtime, every `ppbp-*` skill must verify the official skill is active in the agent's context. If it is not installed or enabled, the agent must strongly recommend the user install it before proceeding — the best-practice guidance in this plugin is additive and assumes the official skill is the foundation.

### The additive-only rule (no restatement)

**A `ppbp-*` skill must never repeat information already specified in the official skill.** This is stricter than "do not contradict": commands, flags, procedures, version pins, API signatures, and step-by-step sequences that the official skill already documents must **not** be duplicated here — even when they are correct today.

**Why:** the official skill is the single source of truth and it evolves. Any content copied from it becomes a latent contradiction the moment the official skill changes (a new CLI flag, a different React version, a renamed command). Duplication is therefore an obsolescence-and-ambiguity bug, not a convenience. The goal is **zero ambiguity** about which instruction an agent should follow: for anything the official skill owns, there must be exactly one place that states it — the official skill.

**What a best-practice skill may contain** — only genuinely *additive* content the official skill does **not** cover:

- Team conventions (naming structures, repository layout, solution/publisher choices).
- Opinionated defaults and decision guidance ("prefer X over Y when…").
- Cross-cutting gotchas and anti-patterns the official skill is silent on.
- Routing/orientation between skills.

**What it must NOT contain** — anything the official skill already specifies. Replace it with a pointer: *"The official skill owns <topic> — load it for the procedure."*

**Authoring test:** for every concrete statement ask *"does the official skill already say this?"* — if yes, delete it and point to the official skill; if no, and it is a useful team convention, keep it. If a skill's additive surface is thin after this pass, the skill must shrink accordingly — never pad it with restated official content.

## Plugin Architecture

### Structure

Skills are distributed as **domain plugins**, not as a flat list. The marketplace `powerplatform-bestpractices` registers N domain plugins; each plugin groups the skills for one technical area (ALM, Code Apps, Dataverse schema, etc.).

```
marketplace: powerplatform-bestpractices
└── plugin: ppbp-<domain>/
    ├── plugin.json
    └── skills/
        ├── ppbp-<domain>-overview/SKILL.md   ← required in every domain plugin
        └── ppbp-<domain>-<task>/SKILL.md     ← one per specific concern
```

### The overview skill

**Every domain plugin must contain exactly one overview skill**, named `ppbp-<domain>-overview` (or `ppbp-dv-<domain>-overview` for Dataverse sub-domains).

The overview skill is the **entry point** for the domain. It must contain:

1. **`## Repository layout`** — the exact directory paths that domain assets live in, with a code block showing the subtree under `<repo-root>/`. This is the **only** skill in the plugin that contains a repo layout section; task skills must not repeat it.
2. **`## Domain scope`** — a table mapping each sibling task skill to a one-line description of what it covers. Agents use this to route to the right skill within the plugin.
3. **`## Global <domain> principles`** — *additive* rules and conventions that apply across all task skills in the plugin (e.g. "always use global Choices", a publisher-prefix scheme, a repo-layout convention). These must be team conventions the official skill does not already state — never a restatement of an official constraint (per the additive-only rule). They are stated once here; task skills do not repeat them.
4. **`## Anti-patterns (DO NOT DO)`** — domain-level anti-patterns that don't belong to a single task skill.
5. **`## Skill boundaries`** — routes out of the plugin to other plugins and to `ppbp-overview`.

The overview skill does **not** contain step-by-step procedures, code examples, or deep guidance — those belong in the task skills.

### Task skills

Task skills cover one specific concern within the domain (e.g. table naming, step plugin implementation, connector integration). They must:

- **Not** contain a `## Repository layout` section — link to the domain overview instead.
- Reference the overview in `## Skill boundaries`: `- Domain orientation and repository layout → ppbp-<domain>-overview`.
- Not repeat global principles already stated in the overview.

### When to create a new plugin vs a new skill

- **New plugin** — a genuinely distinct technical domain with its own repository path, toolchain, or deployment target. Example: a future `ppbp-powerautomate` plugin.
- **New skill in an existing plugin** — a new specific concern within an existing domain. Example: adding `ppbp-dv-relationships` to the `ppbp-dataverse-metadata` plugin.

When in doubt, add a skill to an existing plugin before creating a new plugin.

### plugin.json per domain

Every plugin directory under `.github/plugins/<domain>/` must contain a `plugin.json`:

```json
{
  "name": "ppbp-<domain>",
  "version": "1.0.0",
  "description": "<one-line domain description>",
  "author": { "name": "Théophile Chin-nin", "url": "https://github.com/tchinnin" },
  "homepage": "https://github.com/tchinnin/powerplatform-bestpractices-skills",
  "license": "MIT"
}
```

---

## Skill Authoring Standards

### Language

All content is in English — skill bodies, references, code examples, comments, commit messages.

### Naming

Skill directories and `name` fields follow `ppbp-<concept>` (lowercase, hyphens only). Dataverse-specific skills use the `dv-` infix: `ppbp-dv-<concept>`. The directory name must match `name` exactly.

Within a domain plugin, skills may include a task-level suffix to distinguish granular concerns — for example, `ppbp-dv-tables` and `ppbp-dv-columns` both live inside the `ppbp-dataverse-metadata` plugin. The `ppbp-` prefix remains mandatory on every skill, regardless of its plugin.

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

#### Overview skills (`ppbp-<domain>-overview`)

Required sections (see the **Plugin Architecture** section above for full content rules):

| Section | Required | Notes |
|---|---|---|
| `## Official skill` | Yes | Same rule as task skills |
| `## Repository layout` | Yes | Only this skill in the plugin contains it |
| `## Domain scope` | Yes | Table: skill name → one-line description |
| `## Global <domain> principles` | Yes | Rules shared by all task skills; not repeated in task skills |
| `## Anti-patterns (DO NOT DO)` | Yes | Domain-level only |
| `## Skill boundaries` | Yes | Routes to sibling skills and to `ppbp-overview` |

#### Task skills (all other `ppbp-*` skills)

Required sections:

| Section | Required | Notes |
|---|---|---|
| `## Official skill` | Yes | State the paired official skill, or explicitly note none exists |
| `## Anti-patterns (DO NOT DO)` | Yes | Wrong/Correct mapping tables |
| `## Skill boundaries` | Yes | Must include a line pointing to the domain overview |

- `## Official skill` — state which official Microsoft skill this best-practice skill extends (e.g. `powerplatform:codeapps`), with a one-line summary of what it covers. If no official skill exists for this topic, explicitly state: *"No official Microsoft skill exists for this topic."* Agents must load the official skill before this one when one is available. Every `ppbp-*` skill must check at runtime whether the corresponding official skill is active; if it is not, the agent must strongly recommend the user install it before proceeding.
- `## Anti-patterns (DO NOT DO)` — use **Wrong/Correct mapping tables** to make forbidden patterns unambiguous for agents. Format: **Anti-pattern** — description — *correct approach*.
- `## Skill boundaries` — list what this skill does NOT cover and name the skill to use instead. Always include `- Domain orientation and repository layout → ppbp-<domain>-overview` as the first line.

### Code examples

Code blocks must be complete and executable — no comment-only stubs or placeholder snippets. Language depends on the domain:

| Domain | Expected languages |
|---|---|
| ALM / environment ops | PAC CLI, YAML pipeline |
| Code Apps | TypeScript / React |
| Dataverse Plugins | C# |
| Power Fx | Power Fx |

Large or detailed examples go in `references/`, linked from the body. Reference content must illustrate a pattern, not a specific project implementation.

### Documenting common issues and implementation gotchas

When a topic has a **specific implementation pitfall** — a non-obvious API behaviour, a common error that wastes time, a mandatory multi-step procedure that nothing in the official docs makes obvious — document it using this two-level pattern:

**In SKILL.md (body) — minimal signal, 2–3 sentences max:**
- Name the issue in a dedicated `## Common issue: <topic>` section.
- One sentence explaining why it bites people.
- One sentence pointing to the reference file where the full solution lives.

Example:
```markdown
## Common issue: Global Choices and solutions

Creating a Global Choice via the Web API does not add it to a solution automatically —
a second `AddSolutionComponent` call (ComponentType 9) is required.

If you are scripting Global Choices in a solution context, load
[`references/global-choices-in-solutions.md`](references/global-choices-in-solutions.md)
before writing any code.
```

**In `references/<topic>.md` — the full treatment:**
- Root cause and explanation.
- Step-by-step correct procedure with complete, runnable code snippets.
- Table of wrong syntaxes / error codes and their correct alternatives.
- Execution order or sequencing constraints when relevant.
- A complete idempotent script example at the end.

**Why this split:** the skill body is loaded into every relevant agent context — keeping it token-light prevents waste on sessions that never hit the issue. The reference is loaded on demand, only when the agent (or the user) is actually in that situation.

### Safety and quality controls

For guidance on destructive or irreversible operations (e.g. solution deletion, column removal, environment reset), include a prominent warning block at the top of the relevant section. Skills covering CLI-heavy domains must include Wrong/Correct tables to reduce flag hallucination.

## Skill Scope and Deduplication

Before creating a new skill, verify no existing skill already covers the domain. A new skill must represent a distinct, non-overlapping concern. When in doubt, extend an existing skill rather than creating a near-duplicate. Use the `## Skill boundaries` section of existing skills as the authoritative guide.

## Version Management

This repo uses a two-level versioning structure:

- **Skill level** — update `metadata.version` in the skill's frontmatter whenever the skill body changes.
- **Plugin level** — each domain plugin has its own `plugin.json` under `.github/plugins/<domain>/`. Bump `version` in that file whenever a skill in the plugin changes (treat the plugin version as an aggregate of its skills).
- **Marketplace level** — bump `version` in `.claude-plugin/plugin.json` when a plugin is added, removed, or renamed in the marketplace.

**Semantic versioning rules:**

- **MAJOR** — skill removal, breaking rename, required section changes, routing changes that break existing agent behavior.
- **MINOR** — new skill, new required section, expanded coverage, new metadata field.
- **PATCH** — typo fixes, clarifications, non-breaking rewording, reference additions.

## Commit Conventions

Use prefixes: `feat:`, `fix:`, `refactor:`, `add:`, or `docs:` (no scopes).
