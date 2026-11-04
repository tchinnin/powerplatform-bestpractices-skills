---
name: ppbp-codeapps-react
description: >
  Generic React 19 and TypeScript rules (community standards, react.dev) as applied in
  Power Apps Code Apps: hooks, derived state, effects, list keys, conditional
  rendering, strict typing without non-null assertions, measured performance and
  behaviour-driven tests. Use when the user writes or reviews idiomatic React or
  TypeScript in a Code App — useEffect, useState, useMemo, keys, props typing,
  re-render performance, tests — independently of data access and architecture.
license: MIT
user-invocable: true
model: sonnet
allowed-tools: Read, Bash, Grep, Glob, WebSearch
metadata:
  author: powerplatform-bestpractices
  version: "2.0.0"
---

## Official skill

`code-apps-preview:create-code-app` owns the stack and the React version the
template ships. **Load it first**; if it is not active, **strongly recommend the user
install it**. This skill holds only generic React rules — the ones agents most often
get wrong — and applies them to Code Apps. Authoritative sources: react.dev ("You
Might Not Need an Effect", "Rules of Hooks", "Preserving and Resetting State"),
typescriptlang.org.

Code App-specific rules live in the sibling skills: layers and state placement
(`ppbp-codeapps-architecture`), data and TanStack Query (`ppbp-codeapps-data`),
components and forms (`ppbp-codeapps-components`), errors (`ppbp-codeapps-errors`).

## Effects — only to synchronise with something outside React

- `useEffect` is for external systems: non-React DOM, third-party widgets, timers,
  subscriptions, `document.title`. **Not** for fetching (→ TanStack Query), reacting to
  a click (→ the handler or `mutate(..., { onSuccess })`), deriving a value (→ compute
  during render) or chaining `setState`.
- Always return a cleanup. Effects are StrictMode-safe (idempotent) — never "fix" the
  double mount with a `useRef` flag.
- External subscriptions (viewport, `online`) → `useSyncExternalStore`.

## State — minimal and derived

- Store only the source of truth; compute the rest during render. Prefer one
  `status: "idle" | "editing" | "saving"` to several booleans.
- **Never copy props or server data into state** (except an explicitly named
  `initialXxx`), and never mirror a library flag (`isPending`) in your own state.
- Reset a subtree with `key` (`<SampleForm key={sampleId} />`), not with an effect.
- Immutable updates; functional updater when the next state depends on the previous.
  `useReducer` once a component has several related transitions.

## Hooks

- Rules of Hooks are non-negotiable. A function that calls no hook is not a hook —
  name it without `use`.
- **Honest dependencies.** Never disable `react-hooks/exhaustive-deps`: move the value,
  derive it, or use a functional updater. Destructure stable functions
  (`const { mutate } = useMutation(...)`) rather than depending on a whole object.
- `useRef` for values that must not render; never read or write `ref.current` during
  render.
- React 19: `ref` is a plain prop (no `forwardRef`), `<Context value>` replaces
  `<Context.Provider>`, `use(context)` may be called conditionally.

## Rendering

- **Never define a component inside another** — a new identity each render remounts
  it and loses its state.
- `{count > 0 && …}`, never `{count && …}` (renders `0`). Beyond one ternary, extract a
  variable or an early return.
- Keys: a stable id from the data (the Dataverse GUID). Never the index on a list that
  can be reordered or filtered, never `Math.random()`.
- No heavy computation in JSX; prepare values before `return`. Props `onXxx`,
  internal handlers `handleXxx`.

## Performance — measure first

- Profile with React DevTools before optimising. No blanket `memo` / `useMemo` /
  `useCallback`; with the React Compiler enabled, write plain code.
- **Build lookups once.** Repeated `list.find(...)` per row or per render (e.g. a
  code-to-label lookup inside a cell) becomes a `Map` built once — in a `select`, a
  `useMemo` over the source data, or the mapper — and passed down.
- Values memoised for a dependency array (query keys, table columns, callbacks given
  to memoised children) are the legitimate uses of `useMemo` / `useCallback`.
- Expensive reactive input: `useDeferredValue` / `useTransition`; debounce only when
  each keystroke would hit the server.

## TypeScript

- `strict` + `noUncheckedIndexedAccess` (`ppbp-codeapps-setup`). No `any` (use
  `unknown` + narrowing), no `as` to silence an error, `as never` only in test fixtures.
- **No non-null assertions (`!`).** Replace them with a guard, an early return, a
  discriminated union, or TanStack `skipToken` for a query whose input may be missing.
- Explicit `type Props = {…}`; extend native props with `ComponentProps<"button">`;
  discriminated unions for variants; no `React.FC`; `import type` for types.

## Tests

- **Vitest + React Testing Library**; test visible behaviour (`getByRole`, labels),
  not implementation. No large snapshots.
- The Power Apps SDK does not run outside the host: **mock `src/services/`**, never
  call Dataverse. Query hooks get a fresh `QueryClient` per test (`retry: false`).
- Priorities: pure rules and mappers, then data and action hooks, then components
  with logic.

## Anti-patterns (DO NOT DO)

| Anti-pattern | Correct approach |
|---|---|
| **Fetching in `useEffect` + `useState`.** | A TanStack Query hook (`ppbp-codeapps-data`). |
| **An effect that "reacts" to a state change to save, toast or navigate.** | Do it in the handler or the mutation callback. |
| **Copying props / query data into `useState`**, or mirroring `isPending`. | Derive during render; use the library's flag. |
| **Resetting state with an effect when an id changes.** | `key={id}`. |
| **Disabling `react-hooks/exhaustive-deps`.** | Fix the dependency. |
| **A component defined inside another.** | Module scope, its own file. |
| **`{count && …}`.** | `{count > 0 && …}`. |
| **Index or `Math.random()` as `key`.** | The row's GUID. |
| **`list.find(...)` inside every cell / render.** | A `Map` built once and passed down. |
| **`scope!`, `toDelete!` sprinkled to satisfy the compiler.** | Guards, unions, `skipToken`. |
| **`memo` / `useCallback` everywhere "for performance".** | Measure, then memoise what the profiler shows. |
| **Tests that call Dataverse or snapshot whole pages.** | Mock `src/services/`; assert behaviour. |

## Skill boundaries

- Domain orientation and repository layout → `ppbp-codeapps-overview`
- Layers, folders, where state lives, routing → `ppbp-codeapps-architecture`
- Data access, TanStack Query, FetchXML, Custom APIs → `ppbp-codeapps-data`
- Reuse, tables, async states, forms, accessibility in code → `ppbp-codeapps-components`
- Error model and display → `ppbp-codeapps-errors`
- tsconfig, ESLint, Prettier, bundle → `ppbp-codeapps-setup`
- Auditing a whole app → `ppbp-codeapps-review`
