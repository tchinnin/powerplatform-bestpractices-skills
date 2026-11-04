---
name: ppbp-codeapps-components
description: >
  Component practices for Power Apps Code Apps: search and reuse existing components
  before creating one, extend primitives with variants, promote shared pieces, use one
  shared DataTable and AsyncState so every table, grid and async block renders loading,
  error, empty and no-result states, plus forms (React Hook Form + Zod) and
  code-level accessibility. Use when the user creates or edits a component, table,
  grid, list, dialog, form, filter or input, displays loading / error / empty states,
  duplicates UI code, or reviews keyboard access in a Code App.
license: MIT
user-invocable: true
model: sonnet
allowed-tools: Read, Bash, Grep, Glob, WebSearch
metadata:
  author: powerplatform-bestpractices
  version: "1.0.0"
---

## Official skill

`code-apps-preview:create-code-app` owns the stack; the `starter` template
(`ppbp-codeapps-setup`) brings shadcn/ui (Radix), Tailwind, TanStack Table, sonner and
lucide-react. **Load the official skill first**; if it is not active, **strongly
recommend the user install it**. Branding, tokens and design-level accessibility are
owned by `ppbp-codeapps-uxui`. This skill adds how components are reused, composed
and made robust.

## Reuse before you create

Before writing any component, hook or helper:

1. **Search** — `components/ui/` (primitives and team composites), then `hooks/` and
   `lib/`, then the other features:
   `grep -rli "<concept>" src/components src/hooks src/lib`.
2. **Use or extend** — an existing component with a new prop or a `cva` variant
   (`size`, `tone`, `variant`). Repeated class strings across components are a
   missing variant.
3. **Promote** — a piece used by a **second** feature moves to `components/ui/`
   (component), `hooks/` (hook) or `lib/` (pure helper), the same day.
4. **Create** only when nothing fits, in the narrowest place (the feature), and
   promote later.

Rules that keep reuse possible:

- **Features never import Radix directly.** Every interactive primitive comes from
  `components/ui/` (`dropdown-menu`, `popover`, `command`…); add a missing one through
  the shadcn CLI.
- **No raw HTML for things a primitive covers**: `<Button>` (including
  `variant="link"`), `<Input>`, `<Label>`, `SearchInput`, `FieldGroup`.
- **No local re-implementation** of a shared field, search box, label-plus-control
  block, formatter (`lib/format.ts`) or observer (`hooks/use-infinite-scroll.ts`).
- **Context providers are mounted once** at the root (tooltip, toaster, theme) —
  never inside a reusable component.
- **One component per file**, composition (`children`, slots) over piles of boolean
  props, never a component defined inside another.

## Every async view has four states

Each table, grid, list, card or panel that shows server data renders:

| State | Shows | Never |
|---|---|---|
| **Loading** (`isPending`) | Skeleton shaped like the content | Full-screen spinner, blank area |
| **Error** (first load) | `userMessageOf(error)` + **Retry** (`refetch`) | Raw `error.message`, silent failure |
| **Empty** | Purpose-specific message (and the action to create one, if any) | Same text as "no results" |
| **No results** (filters active) | "No results match the current filters" + **Clear filters** | "No data yet" |
| Success | Content; background refresh as a discreet indicator, never a skeleton | Content replaced by a spinner on refetch |

- **Every list or grid is a `DataTable`**; every other async block is wrapped in
  `AsyncState`. Both decide the state with one shared function, so the app behaves
  the same everywhere. A failed *background* refresh keeps the content and is
  announced by the global toast (`ppbp-codeapps-errors`).
- Infinite lists use `useInfiniteScroll` with a visible **Load more** fallback.

Complete `AsyncState`, `DataTable`, `useInfiniteScroll`, `SearchInput`, `FieldGroup`,
dialog variants and providers:
[`references/data-table.md`](references/data-table.md).

## Forms

- Non-trivial forms (more than two fields, validation, several modes) use **React Hook
  Form + Zod** (`zodResolver`, `z.infer` as the form type) inside a `use<X>Form` hook;
  the component only renders fields. Simple forms may use React 19
  `useActionState` — never both on one form.
- **One component per mode** (create / edit / select) sharing the form hook, rather
  than one dialog switching on a mode flag with a dozen `useState`.
- Use the shadcn `form` primitives (`FormField`, `FormItem`, `FormLabel`,
  `FormControl`, `FormMessage`): they wire labels, `aria-invalid` and
  `aria-describedby`. Focus the first invalid field on submit.
- Submit is disabled while the mutation `isPending` — no separate `submitting` state.
- Client validation is UX; **Dataverse remains the authority**. Server errors for a
  field are mapped with `form.setError` (`ppbp-codeapps-errors` §6). Reset an edit
  form with `key={id}` or `reset(data)`.

## Accessibility in code

Design-level accessibility (contrast, focus style, library choice) is owned by
`ppbp-codeapps-uxui`. In components:

- **Native elements first**: an action is a `<button>`, a navigation a `<Link>`, a
  table a `<table>`. No `onClick` on a `<div>`, `<span>` or `<tr>` without the element
  being a real control.
- **Every pointer action has a keyboard path.** No double-click-only edit: put a
  `<Button variant="link">` (or an "Edit" button) in the row; Enter opens it.
- **Composite widgets come from Radix / cmdk** through `components/ui/` (combobox,
  listbox, menu, dialog). Never hand-roll `role="listbox"` on clickable divs without
  arrow-key navigation.
- A focusable element has a role and an accessible name; icon-only buttons have
  `aria-label`. Announce async changes (`aria-busy`, `role="status"`).
- Lint with `eslint-plugin-jsx-a11y` (`ppbp-codeapps-setup`).

## Anti-patterns (DO NOT DO)

| Anti-pattern | Correct approach |
|---|---|
| **Loading / error / empty JSX rewritten in each table.** | `DataTable` / `AsyncState`. |
| **A table with no empty, no error or no "no results" state.** | The four states, always. |
| **Raw `error.message` in the UI.** | `userMessageOf(error)` + Retry. |
| **A new component without searching** `ui/`, `hooks/`, `lib/` and the features. | Search → extend → promote → create. |
| **A shared piece left inside one feature** (e.g. a hint used by three features). | Promote it to `components/ui/`. |
| **Features importing `@radix-ui/*`** or redefining a field / search box locally. | Primitives and composites from `components/ui/`. |
| **The same class string repeated across dialogs / cards.** | A `cva` variant on the primitive or one `ui/` wrapper. |
| **A provider rendered per instance** (`TooltipProvider` in each tooltip). | One provider at the root. |
| **`IntersectionObserver` or formatter code copied between components.** | `hooks/use-infinite-scroll.ts`, `lib/format.ts`. |
| **A dialog with 11 `useState`, three modes and manual validation.** | `use<X>Form` (RHF + Zod), one component per mode. |
| **Clickable `div` / `span` / `tr` with `tabIndex`**, double-click-only actions, fake listboxes. | Native `<button>`, Radix / cmdk primitives, Enter works. |
| **Raw `<button>` for a link-style action.** | `<Button variant="link">`. |

## Skill boundaries

- Domain orientation and repository layout → `ppbp-codeapps-overview`
- Where components, hooks and rules live (layers, split thresholds) → `ppbp-codeapps-architecture`
- The queries behind a table, paging and counts → `ppbp-codeapps-data`
- Error model, toasts, boundaries, field error mapping → `ppbp-codeapps-errors`
- Branding, design tokens, contrast, design-level accessibility → `ppbp-codeapps-uxui`
- Generic React rules (hooks, effects, keys, TypeScript) → `ppbp-codeapps-react`
- Linters and dependencies → `ppbp-codeapps-setup`
