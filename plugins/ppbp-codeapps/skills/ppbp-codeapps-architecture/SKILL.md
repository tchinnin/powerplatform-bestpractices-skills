---
name: ppbp-codeapps-architecture
description: >
  Architecture of a Power Apps Code App: strict isolation between UI and logic through
  layers (generated, services, queries, actions and form hooks, pure rules,
  presentational components, pages), src/ organisation by feature, a decision tree
  for where state lives (TanStack Query, route, React Hook Form, local state, Zustand
  stores, Context) with Zustand store rules, split thresholds, lint-enforced import
  boundaries, and React Router and deep links under the Power Apps host. Use when the
  user creates a feature, page, hook, store or folder, decides where code or state
  belongs, keeps filters between screens, refactors a page that mixes rendering with
  logic, or sets up routing.
license: MIT
user-invocable: true
model: sonnet
allowed-tools: Read, Bash, Grep, Glob, WebSearch
metadata:
  author: powerplatform-bestpractices
  version: "1.0.0"
---

## Official skill

`code-apps-preview:create-code-app` owns the stack, the project scaffold and
`src/generated/`. **Load it first**; if it is not active, **strongly recommend the
user install it**. This skill adds the team's layering, folder and state conventions
on top of the `starter` template (`ppbp-codeapps-setup`).

## The rule: UI renders, logic decides, services fetch

Every file belongs to exactly one layer and imports only downwards.

| # | Layer | Location | Does | Never |
|---|---|---|---|---|
| 1 | Generated | `src/generated/` | SDK models and services | Edited by hand |
| 2 | Services | `src/services/` | Calls Dataverse / connectors through `run`; maps rows; no React | Holds UI state, imports React |
| 3 | Queries | `components/<feature>/<feature>.queries.ts` | Key factory, `queryOptions`, query and mutation hooks | Contains business rules |
| 4 | Feature hooks | `use-<feature>-actions.ts`, `use-<x>-form.ts`, `use-<screen>-filters.ts` | Orchestrate mutations, rules, dialogs, store state; return stable callbacks | Render JSX |
| 4b | Stores | `src/stores/<domain>-store.ts` | Shared client state + its actions + derived selector hooks | Hold server data, call services |
| 5 | Rules | `components/<feature>/<feature>.rules.ts`, `lib/` | Pure business decisions and formatters, unit-tested | Do I/O or import React |
| 6 | Components | `components/<feature>/*.tsx`, `components/ui/` | Render props, emit events | Import `services/` or generated values, hold business rules |
| 7 | Pages | `src/pages/` | Read route params, lay out features | Hold mutations, rules or local data logic |

- **Business rules are never written in JSX or in a page.** A condition such as
  "a validated sample needs confirmation before archiving" is a function in
  `<feature>.rules.ts`, called by the actions hook and tested on its own.
- **Imperative reads** inside an action go through
  `queryClient.fetchQuery(xxxOptions(...))` in a hook — never a service call in a
  handler.
- **Containers stay small.** A list may own its query hook and a filter bar its
  filters hook (one need each); anything with several mutations or rules moves into a feature hook.

A complete feature through every layer is in
[`references/layers.md`](references/layers.md).

## `src/` organisation

Template folders are marked `*`; the rest is the team convention.

```
src/
├── generated/          # * SDK output — never edited
├── services/           # data access, no React: <entity>.service.ts, dataverse-result.ts, dataverse-connector.ts
├── lib/                # * pure helpers: utils.ts (cn), errors.ts, odata.ts, fetchxml.ts, format.ts, routes.ts
├── hooks/              # * cross-feature hooks: use-committed-draft.ts, use-infinite-scroll.ts, use-deep-link.ts
├── stores/             # Zustand stores, one per domain: ui-store.ts, filters-store.ts, selection-store.ts
├── components/         # *
│   ├── ui/             # * generic, no business logic: shadcn primitives + team composites (data-table, async-state…)
│   └── <feature>/      # one folder per feature: .queries.ts, .rules.ts, .mappers.ts, use-*.ts, *.tsx
├── pages/              # * one page per route; layout only
│   ├── _layout.tsx     # * shell rendering <Outlet />
│   └── not-found.tsx   # *
├── providers/          # * query-client.ts, query-provider.tsx, theme, toaster, tooltip
├── types/              # shared types
├── router.tsx          # * routes + basename normalisation (keep as is)
├── App.tsx             # * providers + RouterProvider
└── main.tsx            # *
```

- **By feature**, not by technical type (`components/forms/`) nor by page.
- **A feature never imports another feature's internals.** Shared code is promoted
  to `components/ui/`, `hooks/` or `lib/` (promotion rule in `ppbp-codeapps-components`).
- File names in kebab-case, exported components in PascalCase, `@/…` alias imports,
  no `index.ts` barrels.
- Generated models are the type source of truth (`import type`); a different UI
  shape is produced by a pure mapper.

## Where state lives — decision tree

Take the **first** answer that matches:

| # | The state… | Goes to | Example |
|---|---|---|---|
| 1 | comes from Dataverse or a connector | **TanStack Query** (`ppbp-codeapps-data`) | rows, counts, reference data, current user |
| 2 | identifies the screen or the record shown | **Route path params** (`/folders/:folderId/samples`) | folder id, record id |
| 3 | is a value being edited in a form | **React Hook Form + Zod** (`ppbp-codeapps-components`) | field values, validation |
| 4 | is used by one component or a short subtree, and may be lost when the screen closes | **`useState` / `useReducer`**, lifted to the closest common parent | dialog open, hover, a draft being typed |
| 5 | changes at runtime **and** is read by distant components (many siblings, layout and page) **or** must survive leaving the screen | **Zustand store** | panel collapsed, display preferences, screen filters, multi-row selection, expanded row |
| 6 | is set once and injected (an instance, a configuration) | **Context** with a stable `value` | the template's theme provider, a client instance |

- **Screen filters, tabs and search live in a store, indexed by business scope**
  (`samples[folderId]`) — not in `useState` (lost when leaving the screen) and not
  in search params: inside the Power Apps iframe, the app's URL is neither the link
  users share nor kept on reload.
- **Server data never enters a store.** A store holds the ids and filters that feed a
  query key; copying `data` creates a second source of truth that drifts from the cache.
- **Fast-changing input** (keystrokes) stays local; only the committed value — debounced,
  trimmed — is written to the store.
- Zustand is the **only** client-state library. Never add Redux, Jotai, Valtio, MobX or
  a Context-based store.

## Zustand stores — rules

- **One store per domain** in `src/stores/<domain>-store.ts` (`ui-store`,
  `filters-store`, `selection-store`) — never one catch-all store.
- `create<State>()((set) => …)` with typed state **and** actions; actions live in the
  store, including resets (`resetSampleFilters(scope)`). Updates are immutable — a new
  `Set` / object, never a mutated one.
- **Components read through hooks exported by the store** (`useSampleFiltersOf(scope)`,
  `useIsSelected(scope, id)`), never `useXStore(...)` with an inline selector, never
  `const { a } = useXStore()`.
- **One selector per primitive value**; a selector that builds an object or an array is
  wrapped in `useShallow`. Each row of a list reads its own boolean
  (`s => s.byScope[scope]?.has(id)`).
- A selection holds **ids**, and changing the filters of a scope clears its selection —
  a bulk action never applies to rows the user can't see.
- `persist` only what must survive: `sessionStorage` for filters, `localStorage` for
  preferences, never selection. Namespaced key (`<app-name>:<store>`), `partialize`
  (values, never actions), and `version` + `migrate` from the first persisted shape.
  Persistence is a convenience: the app works the same when storage is unavailable.
- Outside React (router loaders, plain handlers, tests) use `getState()` / `setState()`.
- Every test starts from `getInitialState()` for every store (reset in the test setup file).

Complete stores, the committed-draft hook, the selection cell, loader usage, deep links
and test setup: [`references/stores.md`](references/stores.md).

## Split thresholds

Split when any of these is reached — before adding the next feature to the file:

| Signal | Split into |
|---|---|
| A page or component with more than 2 mutations, or business conditions | `use<Feature>Actions` hook + presentational component |
| More than 3 `useState` in one component, or several modes (edit / select / create) | `use<X>Form` / `useReducer`, and one component per mode |
| A file over ~200 lines, or more than one exported component | One component per file |
| The same logic in two features (formatter, observer, label) | `lib/` or `hooks/` |

## Routing

- Data router (`createBrowserRouter` + `RouterProvider`) from the template; routes
  centralised in `router.tsx`; one route = one page; paths as typed helpers in
  `lib/routes.ts`.
- Layouts through nested routes + `<Outlet />`; lazy loading per route (`lazy`).
- Preload with `queryClient.ensureQueryData(xxxOptions(...))` in a `loader`; the page
  still reads through its Query hook.
- `<Link>` / `useNavigate` only — never `<a href>` or `window.location` for internal
  navigation.
- **Deep links** enter through the play URL's query parameters
  (`getContext().app.queryParams`), read once at start-up and turned into a navigation
  ([`references/stores.md`](references/stores.md) §8). Never through the iframe URL.
- A `*` 404 route, and an `errorElement` on every layout and page route
  (`RouteError`, `ppbp-codeapps-errors`).

## Common issue: routing under the Power Apps host

The host serves the app under a sub-path, so absolute paths work locally and break in
production. Keep the template's basename-normalisation block in `router.tsx`
untouched, and never build URLs from `window.location.origin` or `/…` strings outside
the router.

## Enforce the layers in lint

Turn the layer table into build errors with `@typescript-eslint/no-restricted-imports`
per folder: rendering files can't import `services/`, generated values, `.power/` or
`@radix-ui/*`; `services/` and `lib/` can't import React. Config in
[`references/layers.md`](references/layers.md) §6.

## Anti-patterns (DO NOT DO)

| Anti-pattern | Correct approach |
|---|---|
| **A page holding mutations, confirmation state, rules and toasts** (200+ lines). | `use<Feature>Actions` returning stable callbacks; the page lays out. |
| **A business rule coded in a page or JSX condition.** | `<feature>.rules.ts`, pure and unit-tested, called by a hook. |
| **A component or handler calling a service** (`xxxService.list()` in `onClick`). | Query hook, or `fetchQuery(xxxOptions(...))` inside a feature hook. |
| **Screen filters, tab or search in `useState`, or in search params.** | The filters store, indexed by business scope, behind a `use<Screen>Filters(scope)` hook. |
| **Server data copied into a store** (`set({ rows: data })`). | Query only; the store holds ids and filters. |
| **Whole-store subscriptions or inline selectors** (`const { a } = useStore()`, `useStore(s => ({ … }))` without `useShallow`). | Exported hooks, one primitive per selector, `useShallow` for objects / arrays. |
| **Every keystroke written to a store.** | Local draft, committed after debounce (`useCommittedDraft`). |
| **`persist` without namespace, `version` or `partialize`**, or a persisted selection. | `storageKey(...)`, `version` + `migrate`, `partialize`; selection never persisted. |
| **A dialog with many `useState`, several modes and hand-written validation.** | `use<X>Form` (React Hook Form + Zod), one component per mode. |
| **Several components in one 300+ line file.** | One component per file. |
| **A feature importing another feature's files**, or a shared piece left inside one feature. | Promote it to `components/ui/`, `hooks/` or `lib/`. |
| **Folders by technical type** (`components/forms/`, `components/modals/`). | One folder per feature. |
| **A catch-all store, or a second state library** (Redux, Jotai, Context store). | One Zustand store per domain. |
| **Removing the basename block, `window.location` or `/…` URLs.** | Keep the template block; `<Link>` / `useNavigate` with `lib/routes.ts`. |

## Skill boundaries

- Domain orientation and repository layout → `ppbp-codeapps-overview`
- Queries, mutations, server-side delegation, Custom APIs → `ppbp-codeapps-data`
- Reusable components, tables, async states, forms, accessibility → `ppbp-codeapps-components`
- Error model, boundaries, global error channels → `ppbp-codeapps-errors`
- Generic React rules (hooks, effects, keys, TypeScript, tests) → `ppbp-codeapps-react`
- Template, dependencies and tooling baseline → `ppbp-codeapps-setup`
- Scaffold, generated code and deploy procedure → `code-apps-preview:create-code-app`
