---
name: ppbp-codeapps-data
description: >
  Dataverse and connector data access in Power Apps Code Apps: every call through a
  service wrapper and TanStack Query, work delegated to the server (native OData, then
  FetchXML through the Dataverse connector, then bound or unbound Custom APIs), bounded
  and paginated lists, counts, writes and cache policy, and the mandatory Dataverse
  call map. Use when the user reads or writes Dataverse from a Code App, writes a query,
  mutation, service, FetchXML or $expand, pages or counts rows, loops over pages,
  updates many rows, calls a Custom API, or touches src/generated/.
license: MIT
user-invocable: true
model: sonnet
allowed-tools: Read, Bash, Grep, Glob, WebSearch
metadata:
  author: powerplatform-bestpractices
  version: "1.0.0"
---

## Official skill

`code-apps-preview:create-code-app` and the `add-*` data-source skills
(`add-dataverse`, `add-connector`, …) own how data sources are added and generated,
and `add-dataverse/references/dataverse-reference.md` owns the Dataverse field rules
(choices, virtual fields, lookups, files, formatted values). **Load them first** and
read `dataverse-reference.md` before writing Dataverse code. If they are not active,
**strongly recommend the user install them**. This skill adds where the work runs,
how calls are shaped, and how they flow through TanStack Query.

> ## 🚨 The server does the work
>
> Filtering, sorting, joining, counting and aggregating happen **in Dataverse**,
> never in the browser. A `queryFn` returns **one bounded page**. Loading many pages
> to filter, count or aggregate in JavaScript — e.g. 30 pages × 500 rows — is
> **forbidden**, whatever the dataset size today. If you need "all rows", you are
> asking the wrong question: ask the server for the answer.

## Rule 0 — every call: service wrapper + TanStack Query

- Every Dataverse or connector call lives in `src/services/` (no React) and goes
  through `run` / `runPage` / `runOrNull` (`ppbp-codeapps-errors`).
- Every read is a `useQuery` / `useInfiniteQuery`; every write is a `useMutation`.
  No exception: no service call from a component, a handler or an effect, and no
  write queue built with refs and state outside `useMutation`.
- **Never edit `src/generated/`** — regenerate through the official `add-*` procedure.
  Never import from `.power/` or through relative paths into generated internals.

## The delegation ladder — go down only when the step above can't do it

| Step | Channel | Use for | Reference |
|---|---|---|---|
| 1 | **Native generated service** (`getAll` with `select`, `filter`, `orderBy`, `maxPageSize` / `top`, `count`) | CRUD, filtered and sorted lists, counts up to 5,000 | [`tanstack-query.md`](references/tanstack-query.md) |
| 2 | **FetchXML through the Dataverse connector** (`shared_commondataserviceforapps`) | Aggregates, `distinct`, `link-entity` with conditions, `exists` on related tables, filters on a collection under a lookup, `$expand` | [`fetchxml.md`](references/fetchxml.md) |
| 3 | **Custom API** — **bound** (one record's scope) or **unbound** (global) | Business processing, one user action → several writes, atomic multi-row updates, rules that must hold for every client, heavy aggregation | [`custom-api.md`](references/custom-api.md); design → `ppbp-dv-custom-api` |

**Don't hesitate to propose a Custom API.** If one user intent produces more than one
write, or a write guarded by a business rule, present a Custom API proposal (name,
bound/unbound, parameters, transaction) instead of orchestrating it in the browser.

## Reads

- **Every list is bounded.** Paged lists use `maxPageSize` + the SDK `skipToken` (or
  FetchXML `count` + `page` + paging cookie) through `useInfiniteQuery`, one page per
  `queryFn` call. Non-paged lists (dropdowns, recent items) use `top` with an order.
  No `getAll()` without a bound.
- **Minimal columns** (`select` / `<attribute>`), deterministic order (a unique last
  sort column).
- **Counts come from the server**: `count: true` on the first page (≤ 5,000), or a
  FetchXML aggregate keyed on the same debounced filters — never `rows.length` of a
  full load.
- **One call per page.** Compute derived flags in the same FetchXML (`link-entity`,
  `exists`). A second call per page needs a platform reason, written in the call map.
- **One query per data need**, keyed on the debounced input — not two queries for the
  "initial" and "typed" values plus a `fetchQuery` on top.
- **Lookups, not N+1.** Resolve related data with `$expand` / `link-entity` or one
  `In(...)` query for a page's ids, never one call per row.
- **Query helpers are shared:** `lib/odata.ts` (`odataString`, `eq`, `inFilter`,
  `and`) and `lib/fetchxml.ts` (`xmlEscape`, `likeContains`, `condition`, …) — never
  rebuilt per service. Payloads are typed against the generated model (no `as never`).

## TanStack Query conventions

- **Every query defined once** with `queryOptions` / `infiniteQueryOptions` in
  `<feature>.queries.ts`, keys from a per-feature factory (including polling and
  mutation keys), reused by hooks, loaders, `fetchQuery` and `ensureQueryData`.
- **Conditional queries use TanStack's `skipToken`** — no `enabled: !!x` + `x!`, no
  "idle" key, no throw in `queryFn` for a missing input.
- **Writes:** `useMutation` with a `mutationKey`, called with `mutate(vars, { onSuccess })`;
  `isPending` drives the UI — no `mutateAsync` + `try/catch`, no `submitting` state.
- **One cache strategy per mutation:** patch the cache with the row the server
  returns (`setQueryData` / `setQueriesData`) **or** invalidate — never both, never a
  manual `refetch()`.
- **`staleTime` chosen per query** from the cache policy table (reference data `∞`,
  edited lists ~30 s, polling `0` + `refetchInterval`).
- `isPending` (no data yet) vs `isFetching` (background) — never `isLoading` for skeletons.

## Writes

- **Atomic multi-row change → Custom API** (plug-in using `UpdateMultiple` /
  `CreateMultiple` in one transaction). N PATCHes from the browser, even with a
  concurrency limit, leave data half-updated when one fails.
- **Bounded concurrency** (`lib/concurrency.ts`) is acceptable only for independent
  writes where partial success is fine and failures can be retried.
- **No find-then-create.** Uniqueness is enforced by an **alternate key**; create and
  handle the `duplicate` error kind, or upsert server-side in a Custom API.
- Use the row returned by `create` / `update` instead of reading it again.

## The call map is mandatory

Every app documents its calls in `docs/<app-name>/dataverse-calls.md`: one row per
call (table, scope, channel, cache) and the calls per user action. Update it in the
same change as any new or modified call. Template:
[`references/call-map.md`](references/call-map.md).

## Common issue: the native client pages 500 rows at a time

`getAll()` without `top` returns a page of 500 rows plus a `skipToken`; looping on
that token silently loads the whole table. Page with `maxPageSize` through
`useInfiniteQuery`, or bound with `top`. Details in
[`references/tanstack-query.md`](references/tanstack-query.md) §1.

## Common issue: FetchXML and `$expand` need the connector

The native client exposes neither, and the official `add-connector` redirects
`commondataservice` to native Dataverse. Add `shared_commondataserviceforapps` as a
connector data source; wrapper and paging cookie handling in
[`references/fetchxml.md`](references/fetchxml.md).

## Common issue: nested `$expand` breaks paging

Expanding a collection inside another collection fails on page 2 with
`Paging Cookie And Query Do Not Match`. Page the ids with FetchXML, then read their
detail in one bounded `$expand` call — [`references/fetchxml.md`](references/fetchxml.md) §5.

## Common issue: refetching an infinite list reloads every page

A refetch replays every cached page sequentially. Trim hidden lists to page 1
(`meta: { firstPageOnly: true }`) and patch the cache on writes —
[`references/tanstack-query.md`](references/tanstack-query.md) §6.

## Common issue: two different `skipToken`s

The SDK's `IOperationResult.skipToken` is a paging cursor; TanStack's `skipToken`
disables a query. Confusing them breaks paging or silently disables fetching —
[`references/tanstack-query.md`](references/tanstack-query.md) §3.

## Anti-patterns (DO NOT DO)

| Anti-pattern | Correct approach |
|---|---|
| **Looping over every page in one `queryFn`** (`while (skipToken)`), then filtering / counting / aggregating in JS. | Server-side filter, FetchXML aggregate, or Custom API; `useInfiniteQuery` for display. |
| **`getAll()` / `listRecords` with no bound**, or `top: 5000` "to be safe". | `maxPageSize` paging or `top` + order sized to the UI. |
| **Filtering, sorting or counting server data in the browser.** | `filter` / `orderBy` / `count`, or FetchXML. |
| **One call per row** (lookup names, flags, children). | `$expand`, `link-entity`, or one `In(...)` call per page. |
| **N updates from the browser for one user action.** | Custom API with `UpdateMultiple` in one transaction. |
| **Find-then-create** on a natural key. | Alternate key + `duplicate` handling, or server-side upsert. |
| **Calling a service from a component or handler** (`service.list…()` in a page). | Query hook, or `queryClient.fetchQuery(xxxOptions(...))` inside a hook. |
| **Raw query objects / keys rewritten inline**, hand-written polling keys. | `queryOptions` + key factory, reused everywhere. |
| **"Idle" keys, `scope!`, throwing in `queryFn` when an input is missing.** | TanStack `skipToken`. |
| **`setQueryData` followed by `invalidateQueries`.** | One strategy per mutation. |
| **`mutateAsync` + `try/catch`, `submitting` state, writes outside `useMutation`.** | `mutate` with callbacks, `isPending`, `mutationKey`. |
| **`staleTime: Infinity` on data other users edit**, or the default left on polled data. | `staleTime` from the cache policy table. |
| **OData `In(...)`, escaping or mapping helpers redefined per service**; `as never` payloads. | `lib/odata.ts`, `lib/fetchxml.ts`, typed payloads. |
| **Hand-editing `src/generated/`** or importing from `.power/`. | Regenerate via the official `add-*` skills. |
| **A new call without updating `docs/<app-name>/dataverse-calls.md`.** | Update the call map in the same change. |

## Skill boundaries

- Domain orientation and repository layout → `ppbp-codeapps-overview`
- Layers and where services, queries and hooks live → `ppbp-codeapps-architecture`
- Error model, `run` / `runOrNull`, global error channels → `ppbp-codeapps-errors`
- Tables, empty / error states, infinite-scroll UI → `ppbp-codeapps-components`
- Custom API design and plug-in implementation → `ppbp-dv-custom-api`, `ppbp-dv-plugins-overview`
- Alternate keys and schema design → `ppbp-dv-tables`, `ppbp-dv-columns`
- Adding data sources, generated files, Dataverse field rules → `code-apps-preview:add-dataverse` and the other `add-*` skills
