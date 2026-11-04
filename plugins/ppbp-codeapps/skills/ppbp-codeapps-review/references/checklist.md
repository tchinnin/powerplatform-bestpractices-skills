# Code App review checklist

Each check names the skill that owns the rule. Default priority: **P1** = correctness,
data integrity or Dataverse load; **P2** = maintainability, consistency, UX;
**P3** = quality and tooling. Raise or lower a finding only with a stated reason
(scale, user impact).

Useful sweeps are given in `code` — run them from `codeapps/<app-name>/`.

## P1 — errors and data layer

### Errors (`ppbp-codeapps-errors`)

- [ ] No service swallows errors: no `catch { return null }` / `catch { return [] }`; `null` only via `runOrNull` for `notFound`.
      `grep -rn "catch" src/services`
- [ ] One `services/dataverse-result.ts`; no `toError` / `unwrap` / `call` / `check` redefined per service.
      `grep -rn "function \(toError\|unwrap\|call\|check\)" src/services`
- [ ] Errors classified by Dataverse code / HTTP status in `lib/errors.ts`, never by regex on message words.
      `grep -rn "test(.*message\|/duplicate\|/already\|in progress" src`
- [ ] `MutationCache` / `QueryCache` `onError` configured; no `toast.error` inside mutation hooks or components.
      `grep -rn "toast.error" src --include=*.ts --include=*.tsx`

### Data (`ppbp-codeapps-data`)

- [ ] No `queryFn` / service loops over pages (`while (skipToken)`, `do … while`, recursive paging).
      `grep -rn "skipToken\|while (" src/services src/components`
- [ ] Every `getAll` / `listRecords` / FetchXML is bounded (`maxPageSize` paging or `top` + order); no "load up to 5000".
- [ ] No filtering, sorting, counting or aggregating of server data in the browser (`.filter(` / `.reduce(` / `.length` on full loads).
- [ ] No N+1 (a call per row, per lookup, per child).
- [ ] No set of writes for one user action sent from the browser when it must be atomic → Custom API proposed.
      `grep -rn "Promise.all\|forEachConcurrent" src`
- [ ] No find-then-create on a natural key (alternate key + `duplicate` handling, or server-side upsert).
- [ ] FetchXML / OData values escaped through `lib/fetchxml.ts` / `lib/odata.ts`.
- [ ] `docs/<app-name>/dataverse-calls.md` exists and matches the services and query keys.
- [ ] Nothing edited under `src/generated/`; no import from `.power/`.

## P2 — TanStack Query, state, architecture, components

### TanStack Query (`ppbp-codeapps-data`)

- [ ] Every query built with `queryOptions` / `infiniteQueryOptions`; no inline `{ queryKey, queryFn }` duplicates (including in `fetchQuery`).
      `grep -rn "queryKey:" src --include=*.tsx`
- [ ] Every key from a factory, polling and mutation keys included; no string or hand-built keys.
- [ ] Conditional queries use TanStack `skipToken`; no "idle" keys, no `!`, no throw for a missing input.
- [ ] Writes through `useMutation` with a `mutationKey`; no write queue outside it; `mutate` with callbacks, no `mutateAsync` + `try/catch`.
      `grep -rn "mutateAsync" src`
- [ ] No state mirroring `isPending` (`submitting`, `saving`).
- [ ] One cache strategy per mutation (no `setQueryData` + `invalidateQueries`); no manual `refetch()` after a write.
- [ ] `staleTime` chosen per query (reference data `∞`, edited lists short); `isPending` not `isLoading`.
- [ ] One query per data need (no duplicate queries for initial vs typed value); count not refired per keystroke.
- [ ] Hidden infinite lists trimmed to page 1 (`meta.firstPageOnly`).

### Architecture and state (`ppbp-codeapps-architecture`)

- [ ] No component / page / handler calls a service or a generated service.
      `grep -rln "@/services/\|generated/services" src/components src/pages --include=*.tsx`
- [ ] No business rule inside a page or JSX; rules in `<feature>.rules.ts`, tested.
- [ ] Pages: layout only — no more than 2 mutations, no confirmation logic → `use<Feature>Actions`.
- [ ] State placed by the decision tree: server data in Query, screen / record identity in route params, forms in React Hook Form, local state local, shared or cross-screen client state in a Zustand store, injected values in Context.
- [ ] Screen filters, tabs and search in the filters store indexed by business scope — not `useState`, not search params.
      `grep -rn "useSearchParams" src`
- [ ] No server data in a store (`set({ rows`, `set({ data`); stores hold ids and filters only.
      `grep -rn "set(" src/stores`
- [ ] Stores: one per domain in `src/stores/`; read through exported hooks; one primitive per selector or `useShallow`; no whole-store destructuring; immutable updates (new `Set`).
      `grep -rn "Store()" src --include=*.tsx`
- [ ] Keystrokes kept local, only committed values in stores; changing filters clears the scope's selection.
- [ ] `persist`: namespaced key, `version` + `migrate`, `partialize`; selection not persisted.
- [ ] No second state library (Redux, Jotai, Valtio, MobX, Context store).
- [ ] Feature folders don't import each other's internals; shared pieces promoted.

### Components (`ppbp-codeapps-components`)

- [ ] Every list / grid is a `DataTable`; every other async block an `AsyncState`.
- [ ] Each async view handles loading, error (with Retry), empty **and** no-results (with Clear filters).
- [ ] No raw `error.message` displayed.
      `grep -rn "error.message\|error?.message" src/components src/pages`
- [ ] No duplicated UI piece (search input, label + control, dialog classes, infinite-scroll observer, formatter).
- [ ] No `@radix-ui/*` import outside `components/ui/`.
      `grep -rln "@radix-ui" src/components src/pages | grep -v components/ui`
- [ ] Providers mounted once (no `TooltipProvider` per instance).
- [ ] Forms with RHF + Zod in a `use<X>Form`; one component per mode; server errors mapped to fields.
- [ ] Accessibility: no clickable `div` / `span` / `tr`, every pointer action has a keyboard path, composite widgets from Radix / cmdk, icon buttons labelled.
      `grep -rn "onClick" src --include=*.tsx | grep -v "<Button\|<button\|<Link"`

### React (`ppbp-codeapps-react`)

- [ ] No fetching or action logic in `useEffect`; effects clean up.
- [ ] No copied props / server data in state; reset with `key`.
- [ ] No component defined inside another; stable keys; no `{n && …}`.
- [ ] No `list.find` per row / render where a `Map` would do.

## P3 — quality and tooling

### Setup (`ppbp-codeapps-setup`)

- [ ] `eslint-plugin-react-hooks` v7+, `jsx-a11y`, `@tanstack/eslint-plugin-query`, layer rules, `ecmaVersion: "latest"`.
- [ ] Prettier configured (with the Tailwind plugin); formatting consistent.
- [ ] `noUncheckedIndexedAccess` on; no unjustified `!`.
      `grep -rn "[a-zA-Z)]\!\.\|[a-zA-Z)]\![,;)]" src --include=*.ts --include=*.tsx`
- [ ] React Query Devtools, lazy and dev-only.
- [ ] No chunk over 500 kB (`npm run build` output).
- [ ] `npm run lint`, `npm run build`, `npm run test` green.

### Code quality

- [ ] One component per file; no file over ~200 lines with several components.
- [ ] Shared formatters in `lib/format.ts`; no raw `<button>` for a link-style action.
- [ ] Unusual choices documented in a comment (e.g. a download implemented as a mutation).
- [ ] No `console.*` outside the logging sink.
