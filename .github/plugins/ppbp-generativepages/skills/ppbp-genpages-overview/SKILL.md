---
name: ppbp-genpages-overview
description: >
  Power Apps Generative Pages — team conventions and orientation. Use when starting a
  Generative Page task in a model-driven app to decide where page sources live in the
  repo, how to name pages, and when to split one page into several. All authoring,
  runtime APIs, dependencies, and deployment are owned by the official model-apps:genpage
  skill — this skill routes to it and adds only repo and team conventions.
license: MIT
metadata:
  author: powerplatform-bestpractices
  version: "1.1.0"
---

## Official skill

`model-apps:genpage` — owns the **entire** Generative Page procedure: scaffolding,
the single-`.tsx` page model, the React / TypeScript / Fluent UI dependency set, the
runtime surface (the `Xrm` global plus the `dataApi` / `pageInput` props), the
authoring rules, and deployment into a model-driven app. Load it for everything you
build. If it is not active, **strongly recommend the user install it** before
proceeding. This skill never restates its APIs, versions, commands, or rules — those
live in the official skill and evolve over time; it adds only the repo-organisation
and team conventions below.

## Repository layout

The official tool manages its own working directory. For version control, keep a
curated copy of each page's source organised by the model-driven app it belongs to:

```
<repo-root>/
└── genpages/
    └── <model-app-name>/      # group pages by the model-driven app that hosts them
        └── <page-name>/       # one folder per page
```

- Group by model-driven app — never drop page folders loose under `genpages/`.
- One page, one folder.

## Domain scope

This plugin is a single overview skill. Everything procedural — building, running,
and deploying a page — is owned by `model-apps:genpage`; load it directly.

## Team conventions (additive only)

1. **Naming** — name each page folder for the app and the job it does (e.g.
   `<app>-<entity>-summary`), so the repo reflects where the page is surfaced.
2. **When to split a page** — if a page serves more than one distinct task or
   audience, split it into separate pages rather than branching heavily inside one
   `.tsx`. Smaller pages are easier to review, deploy, and reason about.
3. **Solution placement** — keep a model-driven app's pages in that app's solution;
   see `ppbp-alm-solutions` for solution structure.

## Anti-patterns (DO NOT DO)

| Anti-pattern | Correct approach |
|---|---|
| Page folders loose under `genpages/` — loses the model-app grouping. | Always `genpages/<model-app-name>/<page-name>/`. |
| Restating genpage's runtime APIs, dependency versions, or deploy commands here — drifts when the official skill changes. | State them nowhere here; point to `model-apps:genpage`. |

## Skill boundaries

This skill covers Generative Pages repo organisation and team conventions only. It does not cover:

- All page authoring, runtime APIs, dependencies, and deployment → `model-apps:genpage`
- Standalone Code Apps (canvas / React + Vite) → `ppbp-codeapps-overview`
- Dataverse schema design → `ppbp-dv-tables`, `ppbp-dv-columns`
- Solution lifecycle → `ppbp-alm-solutions`
- Project repository layout → `ppbp-overview`
