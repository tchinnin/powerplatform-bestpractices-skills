---
name: ppbp-codeapps-review
description: >
  Read-only quality review of an existing Power Apps Code App against the ppbp
  Code App conventions — error handling, Dataverse data access and load, TanStack
  Query usage, state placement, UI/logic isolation, component reuse, async states,
  accessibility, typing, tooling and bundle — with a report ranked P1 / P2 / P3 and a
  suggested order of work. Use when the user wants to review, audit, assess or
  challenge a Code App, a pull request on one, or asks "what should we fix first".
license: MIT
user-invocable: true
model: sonnet
allowed-tools: Read, Bash, Grep, Glob, WebSearch
argument-hint: "<app-name or path>"
metadata:
  author: powerplatform-bestpractices
  version: "1.0.0"
---

## Official skill

`code-apps-preview:create-code-app` and the `add-*` skills own the stack, the
generated code and the Dataverse field rules. **Load them before reviewing**; if they
are not active, **strongly recommend the user install them**. This skill only judges
an app; it never changes one.

## What this skill adds

Lint and the compiler catch mechanical errors. This review covers the **judgement**
they can't make: whether data work runs on the server, whether a write must be
atomic, whether an error can be mistaken for "not found", whether logic leaks into
pages, whether a component already exists elsewhere.

**Rule source:** the sibling skills are the only corpus. Read the ones you need before
reviewing, and don't invent rules:

| Area | Source |
|---|---|
| Layout, global principles, call map location | `ppbp-codeapps-overview` |
| Error model, result module, channels, boundaries | `ppbp-codeapps-errors` |
| Server-side delegation, Query conventions, writes, cache, call map | `ppbp-codeapps-data` |
| Layers, state placement, split thresholds, routing | `ppbp-codeapps-architecture` |
| Reuse, `DataTable` / `AsyncState`, forms, accessibility | `ppbp-codeapps-components` |
| Generic React / TypeScript | `ppbp-codeapps-react` |
| Tooling, bundle | `ppbp-codeapps-setup` |

A real problem no rule covers is reported as a finding marked "(no rule yet)", with a
suggestion to add the rule to the right skill.

## Procedure

1. **Scope.** Resolve the app (`codeapps/<app-name>/`, or the path or PR given). If
   several apps exist and none is named, ask. Announce:
   *"Reviewing <app-name>: N features, M services, K query modules."*
2. **Map the layers.** List `src/services/`, `src/components/*/`, `src/pages/`,
   `src/hooks/`, `src/lib/`, `src/providers/`. Read the providers (`QueryClient`
   config), the result / error modules and every service first — P1 findings live there.
3. **Inventory the Dataverse calls.** For each service function: table, channel
   (native, FetchXML, Custom API), bound, columns, calls per user action. Compare with
   `docs/<app-name>/dataverse-calls.md` — a missing or stale call map is a finding.
4. **Walk the checklist** in [`references/checklist.md`](references/checklist.md),
   P1 to P3, using its sweeps to find candidates, then **read each candidate** before
   reporting it.
5. **Check the tooling** from files only: `package.json`, `eslint.config.js`,
   `tsconfig.app.json`, Prettier config. Run `npm run build` / `npm run lint` only if
   the user agrees — the review itself is read-only.
6. **Report** in the format of [`references/report-format.md`](references/report-format.md):
   one table per priority, numbered findings, file and line range, observable
   consequence, one concrete fix with its owning skill, then a suggested order of work.
7. **Hand off.** Offer to fix findings in the suggested order, one group at a time, with
   the user's confirmation. Proposed Custom APIs go through `ppbp-dv-custom-api`.

## Priorities

| Priority | Meaning | Typical findings |
|---|---|---|
| 🔴 P1 | Wrong behaviour, data integrity, or Dataverse load | Swallowed errors, duplicated error logic, unbounded or client-side data work, non-atomic multi-row writes, no global error channel |
| 🟠 P2 | Maintainability, consistency, UX | Query conventions, state misplaced (filters in `useState`, server data in a store), oversized pages / dialogs, duplicated UI, missing states, accessibility gaps, N+1 or extra calls |
| 🟡 P3 | Quality and tooling | Lint / Prettier / tsconfig baseline, Devtools, bundle size, file splits, small duplications, missing comments |

Accessibility blockers (an action impossible with the keyboard) may be raised to P1
with that reason.

## Anti-patterns (DO NOT DO)

| Anti-pattern | Correct approach |
|---|---|
| Editing code during the review. | Read-only; offer fixes afterwards, with confirmation. |
| Reporting a sweep hit without reading the code. | Every finding is read and confirmed. |
| Reporting respected conventions or documented, justified exceptions. | Real deviations only — no false positives. |
| One finding per occurrence of the same defect. | One finding listing every location. |
| A finding without consequence or without a concrete fix. | Consequence + one fix + owning skill. |
| Inventing rules. | Use the sibling skills; mark gaps "(no rule yet)". |
| Querying Dataverse or deploying to check behaviour. | Review the code and the call map. |

## Skill boundaries

- Domain orientation and repository layout → `ppbp-codeapps-overview`
- The rules being checked → `ppbp-codeapps-errors`, `ppbp-codeapps-data`, `ppbp-codeapps-architecture`, `ppbp-codeapps-components`, `ppbp-codeapps-react`, `ppbp-codeapps-setup`
- Design and branding review → `ppbp-codeapps-uxui`
- Custom API design for proposed server-side processing → `ppbp-dv-custom-api`
- Dataverse model review → `ppbp-dv-metadata-review`
