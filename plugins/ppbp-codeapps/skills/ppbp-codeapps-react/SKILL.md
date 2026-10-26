---
name: ppbp-codeapps-react
description: >
  React best practices (React 19, community standards) applied to a Power Apps
  Code App built on the starter template. Covers src/ organisation, React Router
  under the Power Apps host, components, hooks, state, effects, server state with
  TanStack Query over the generated services, typing, forms, performance,
  accessibility, security, tooling and tests. Use when the user writes, reviews or
  refactors React code in a Code App, or hesitates on an idiomatic pattern that
  must stay compatible with the Power Apps SDK.
license: MIT
user-invocable: true
model: sonnet
allowed-tools: Read, Bash, Grep, Glob, WebSearch
metadata:
  author: powerplatform-bestpractices
  version: "1.0.0"
---

## Official skill

`code-apps-preview:create-code-app` owns the stack and the SDK workflow; the
`add-*` skills (`add-dataverse`, `add-connector`, …) own data-source generation,
and `add-dataverse/references/dataverse-reference.md` owns the Dataverse field
rules (choice integers, virtual `…name` fields, lookup read/write, file/image
methods, formatted values). **Load them first** and read `dataverse-reference.md`
before writing Dataverse code. If they are not active, **strongly recommend the
user install them**. This skill only adds React conventions they leave open.

Authoritative external references: react.dev ("Thinking in React", "You Might Not
Need an Effect", "Rules of Hooks", "Preserving and Resetting State"),
tanstack.com/query v5 (and TkDodo's "Practical React Query"), reactrouter.com.

Rules specific to the Code App host are tagged **[Code App]**; the rest is
generic React.

## Baseline stack

Apps are scaffolded from the Microsoft `starter` template, with Zustand removed —
see `ppbp-codeapps-setup`. That gives: React 19, Vite, Tailwind v4, shadcn/ui
(Radix), React Router (data router), TanStack Query, TanStack Table, sonner,
date-fns, lucide-react, recharts. Use these; do not add a competing library for
a concern they already cover.

## `src/` organisation

Template folders are marked `*`; the rest is the team convention.

```
src/
├── generated/          # [Code App] SDK output — never edited (official rule)
├── components/         # *
│   ├── ui/             # * shadcn primitives — generic, no business logic
│   └── <feature>/      # business components, ONE folder PER FEATURE
│       ├── sample-table.tsx
│       ├── sample-form.tsx
│       ├── samples.queries.ts   # query keys + queryOptions + Query hooks
│       ├── samples.mappers.ts   # pure generated-model ⇄ UI-model mapping
│       └── types.ts
├── pages/              # * one page per route; composes features, reads params
│   ├── _layout.tsx     # * shared shell rendering <Outlet />
│   └── not-found.tsx   # *
├── providers/          # * query-provider, theme-provider, sonner-provider
├── hooks/              # * cross-feature hooks
├── services/           # [Code App] thin wrappers OVER generated/services, no React
├── lib/                # * utils.ts (cn) + pure helpers, constants
├── types/              # shared types
├── router.tsx          # * routes + basename normalisation (keep as is)
├── App.tsx             # * providers + RouterProvider
└── main.tsx            # *
```

- **File names in kebab-case** (template + shadcn style), exported components in
  PascalCase.
- **By feature, not by technical type or by page**: no `components/forms/`,
  `components/modals/`; a feature can serve several pages.
- **Dependency direction**: `pages → components/<feature> → components/ui → lib`,
  and `components/<feature> → services → generated`. A feature never imports
  another feature's internals; shared code is promoted to `ui/`, `hooks/` or `lib/`.
- `components/ui/` never imports `generated/`.
- **Thin pages**: compose, read route params, delegate.
- `components/ui/` is managed by the shadcn CLI — add primitives through it.
- `@/…` alias imports; no giant `index.ts` barrels (break tree-shaking, create cycles).
- **[Code App]** Import generated models as the type source of truth
  (`import type`); never redeclare them. Need a different shape → pure mapper.
  Explore large generated files with `grep` rather than reading them whole.

## Routing

- Data router (`createBrowserRouter` + `RouterProvider`), as in the template.
  Routes centralised in `router.tsx`; one route = one page; paths as typed
  constants/helpers.
- Layouts through nested routes + `<Outlet />`; lazy loading per route (`lazy`).
- Preload in a `loader` with `queryClient.ensureQueryData(xxxOptions(...))`; the
  component then reads through its Query hook — the cache stays the source of
  truth, not `useLoaderData`.
- `<Link>` / `<NavLink>` / `useNavigate` only — never `<a href>` or
  `window.location` for internal navigation.
- **Shareable view state in the URL** (filters, sort, page, tab, selected id) via
  `useSearchParams`; parse and validate it with defaults.
- A `*` 404 route and an `errorElement` per route / layout.

## Common issue: routing under the Power Apps host

**[Code App]** The host serves the app under a sub-path, so absolute paths break
in production while working locally. Keep the template's basename-normalisation
block in `router.tsx` untouched, and never build URLs from
`window.location.origin` or from `/…` paths outside the router.

## Components

- **Single responsibility** — no god component mixing layout, fetching, business
  logic and UI. Split container (data hook) from presentation (props) when it helps.
- **Composition over configuration** — `children`, slots, rather than piles of
  boolean props.
- One component per file; **never define a component inside another** (new
  identity each render → remount, lost state).
- No heavy logic in JSX; compute before `return`. Conditional render with
  `{count > 0 && …}`, never `{count && …}`.
- Props `onXxx`, internal handlers `handleXxx`. Function components only
  (error boundaries via `react-error-boundary`).
- **Reuse and extend primitives** from `components/ui/` (new variant/size/prop)
  rather than forking a one-off or writing a raw `<button>`. Look for an existing
  component before creating one. Styles via Tailwind classes merged with `cn()`.

## Hooks

- Rules of Hooks are non-negotiable. A function that calls no hook is not a hook.
- **Honest dependencies** — never disable `react-hooks/exhaustive-deps`; fix the
  cause (move the value, derive it, use a functional updater).
- One responsibility per hook; typed, named return (object if > 2 values).
- `useRef` for values that must not trigger a render; never read/write
  `ref.current` during render.
- React 19: `ref` is a plain prop (no `forwardRef`), `<Ctx value>` replaces
  `<Ctx.Provider>`, `use(context)` may be called conditionally.

## State

- **Minimal and derived** — store only the source of truth; prefer one
  `status: 'idle' | 'editing' | 'saving'` over several booleans.
- Never copy props or server data into state (except an explicit `initialXxx`).
- Reset state with `key` (`<SampleForm key={sampleId} />`), not with an effect.
- Colocate; lift only what is shared. Immutable updates, functional updater when
  the next state depends on the previous one. `useReducer` for multi-transition state.
- **Three kinds of state, three tools — no global store library:**

| State | Tool |
|---|---|
| Server (Dataverse, connectors) | TanStack Query |
| Shareable view state | URL (`useSearchParams`, route params) |
| Local UI | `useState` / `useReducer`; Context only for slow-changing cross-cutting values (theme, current user), with a memoised `value` |

## Effects

- `useEffect` is for **synchronising with an external system** (non-React DOM,
  third-party widget, timers, subscriptions, `document.title`). Not for fetching
  (→ Query), reacting to a click (→ handler), deriving values (→ render) or
  chaining `setState`.
- Always clean up. Be StrictMode-safe (idempotent effects) — never "fix" the
  double mount with a `useRef` flag.
- External subscriptions (viewport, `online`) → `useSyncExternalStore`.
- Logic triggered by a user action (save, toast, navigation) lives in the handler
  or the mutation's `onSuccess`, not in an effect watching state.

## Server state: TanStack Query over the generated services

All data access goes through TanStack Query v5 — **no `useEffect` + `useState`
fetching**. Core rules:

- **[Code App]** One `unwrap(result)` helper in `src/services/` turns a failed
  `IOperationResult` into a thrown `Error`, so Query sees real errors. Components
  never call a generated service directly.
- **[Code App]** Every `getAll` passes a minimal `select`, and pushes `filter` /
  `orderBy` / `top` to the server rather than filtering thousands of rows client-side.
- One `QueryClient`, created outside render, in `providers/query-provider.tsx`;
  start from the template `defaultOptions` and override per query. Global error
  handling through `QueryCache` / `MutationCache` `onError` (sonner toast).
- **Per-feature hierarchical key factory** + exported `queryOptions(...)` in
  `<feature>.queries.ts`; every variable the `queryFn` uses is in the key.
- **One hook per resource** (`useSamples(filters)`, `useSample(id)`); components
  never call `useQuery` directly. Never copy `data` into state — derive or use `select`.
- `isPending` → skeleton; `isFetching` → discreet indicator. Always render
  loading / error (with retry) / empty / success.
- Mutations in dedicated hooks; on success **invalidate and return the promise**
  (or `setQueryData`), never a manual `refetch()`. Prefer `mutate` over `mutateAsync`.

## Common issue: two different `skipToken`s

**[Code App]** The SDK returns a pagination `skipToken` on `IOperationResult`,
while TanStack Query exports an unrelated `skipToken` that disables a query —
mixing them up silently breaks paging or disables fetching.

The full Query setup (unwrap helper, key factory, read/infinite/mutation hooks,
optimistic updates, Suspense, testing) is in
[`references/tanstack-query.md`](references/tanstack-query.md) — load it before
writing data-access code.

## Lists and performance

- `key` = stable id from the data (Dataverse GUID); never the index on a
  reorderable/filterable list, never `Math.random()`.
- Long lists: server pagination first, `@tanstack/react-virtual` second.
- **Measure before optimising** (React DevTools Profiler). No blanket
  `memo` / `useMemo` / `useCallback`; with the React Compiler enabled, write plain
  idiomatic code.
- Expensive reactive input: `useDeferredValue` / `useTransition`; debounce only
  when each keystroke would hit the server.
- **[Code App]** The bundle is loaded inside the Power Apps host: code-split per
  route and watch the `vite build` output.

## TypeScript

- `strict` (+ `noUncheckedIndexedAccess`). No `any` (use `unknown` + narrowing),
  no `as` to silence errors, no unjustified `!`.
- Explicit `type Props = {…}`; extend native props with `ComponentProps<'button'>`
  for primitives; discriminated unions for state/prop variants; no `React.FC`.
- `import type` for types.

## Forms

- Non-trivial forms: **React Hook Form + Zod** (`zodResolver`, `z.infer` as the
  form type). Simple forms may use React 19 `useActionState` / `useFormStatus` —
  never both approaches on the same form.
- Every field has a `<label htmlFor>`; errors wired with `aria-invalid` /
  `aria-describedby`; focus the first invalid field.
- Disable submit while the mutation `isPending`; no double submission.
- Client validation is UX — **Dataverse remains the authority**; surface server
  errors cleanly. Reset an edit form with `key={id}` or `reset(data)`.

## Accessibility, robustness, security

Design-level accessibility (contrast, accessible library choice) is owned by
`ppbp-codeapps-uxui`. In code:

- Semantic HTML first; `aria-*` complements, never replaces. No clickable `div`.
  Don't re-implement keyboard/focus for menus, dialogs, comboboxes — use the
  Radix-based primitives. Announce async changes (`aria-live`, `aria-busy`);
  `aria-label` on icon buttons.
- Error boundaries at the root and around independent zones, reset through
  `QueryErrorResetBoundary`. Render stays pure.
- No `dangerouslySetInnerHTML` on Dataverse/user content (otherwise sanitise
  with DOMPurify).
- Nothing secret in the front end — the bundle and every `VITE_*` variable are
  public. **[Code App]** No API key or token: go through connectors.
- Hiding a button is comfort, not security — Dataverse security roles enforce access.
- No `console.log` left in production; log errors centrally.

## Tooling and tests

- ESLint flat config from the template; **upgrade `eslint-plugin-react-hooks` to
  v6+** (the template ships v5) for the React Compiler rules; add
  `eslint-plugin-jsx-a11y` and `@tanstack/eslint-plugin-query`. Prettier with
  `prettier-plugin-tailwindcss`. Exclude `src/generated/` from lint/format.
- `npm run lint` and `npm run build` green before every commit.
- **Vitest + React Testing Library**; test visible behaviour (`getByRole`), not
  implementation; no massive snapshots.
- **[Code App]** The SDK does not run outside the host: **mock the
  `src/services/` layer** in tests, never call Dataverse.
- Priorities: pure mappers/helpers, data hooks, components with logic.

A review checklist is in
[`references/review-checklist.md`](references/review-checklist.md).

## Anti-patterns (DO NOT DO)

| Anti-pattern | Correct approach |
|---|---|
| **Fetching in `useEffect` + `useState`** — races, no cache, no dedup. | A Query hook over `queryOptions` from the feature's `.queries.ts`. |
| **Calling a generated service from a component** — leaks SDK shape and unchecked `IOperationResult` into UI. | Component → Query hook → `src/services/` wrapper (`unwrap`) → generated service. |
| **Adding Zustand / Redux / another global store** — duplicates the server cache and URL state. | Query for server state, URL for view state, `useState`/Context for local UI. |
| **Copying Query `data` or props into `useState`** — stale, contradictory state. | Derive at render or via Query `select`; reset with `key`. |
| **Manual `refetch()` after a mutation** — misses other keys, races. | `invalidateQueries` on the key factory (return the promise) or `setQueryData`. |
| **String-concatenated query keys** (`'samples-' + id`). | Hierarchical array keys from a per-feature factory. |
| **Folders by technical type** (`components/forms/`, `components/modals/`). | One folder per feature under `components/`. |
| **Removing/editing the basename block or using `/…` / `window.location` URLs** — breaks under the Power Apps host. | Keep the template block; navigate with `<Link>` / `useNavigate`. |
| **Component defined inside another component.** | Move it to its own file / module scope. |
| **Disabling `react-hooks/exhaustive-deps`.** | Fix the dependency cause. |
| **`{count && …}`** — renders `0`. | `{count > 0 && …}`. |
| **Index or `Math.random()` as list `key`.** | Dataverse GUID. |
| **Calling Dataverse in tests.** | Mock `src/services/`. |

## Skill boundaries

- Domain orientation and repository layout → `ppbp-codeapps-overview`
- Scaffold template choice, dependencies, configuration → `ppbp-codeapps-setup`
- Generated-code hygiene and bundle size → `ppbp-codeapps-connectors`
- Branding, design tokens, accessibility at design level → `ppbp-codeapps-uxui`
- Dataverse field rules (choices, virtual fields, lookups, files/images) → `code-apps-preview:add-dataverse` (`dataverse-reference.md`)
- Scaffold / init / data-source / deploy procedure → `code-apps-preview:create-code-app` and `add-*` skills
- Dataverse schema design → `ppbp-dv-metadata-overview`
