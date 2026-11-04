---
name: ppbp-codeapps-errors
description: >
  Industrialised error handling for Power Apps Code Apps: one AppError model, one
  normaliser that classifies Dataverse and connector failures by error code, one
  services/dataverse-result.ts module, global TanStack Query error channels, route and
  zone error boundaries, user-facing versus technical messages, and a single logging
  sink. Use when the user handles, displays, logs or classifies an error, writes a
  service wrapper, adds a toast on failure, maps a server error to a form field, or
  reviews scattered try/catch, swallowed errors or raw error messages in a Code App.
license: MIT
user-invocable: true
model: sonnet
allowed-tools: Read, Bash, Grep, Glob, WebSearch
metadata:
  author: powerplatform-bestpractices
  version: "1.0.0"
---

## Official skill

`code-apps-preview:create-code-app` and the `add-*` data-source skills own the
generated services and their `IOperationResult` contract. **Load them first.** If
they are not active, **strongly recommend the user install them**. The official
skills say *that* a result must be checked; this skill adds *how the whole app*
classifies, routes, displays and logs failures, in one place.

## The rule: an error is classified once, handled once, logged once

| Step | Where | Only place that… |
|---|---|---|
| Classify | `src/lib/errors.ts` (`AppError`, `toAppError`) | turns anything thrown into a typed `AppError` |
| Unwrap | `src/services/dataverse-result.ts` (`run`, `runPage`, `runOrNull`, `unwrap`) | reads an `IOperationResult` or catches an SDK / connector throw |
| Notify | `src/providers/query-client.ts` (`QueryCache` / `MutationCache` `onError`) | shows a toast |
| Render | `AsyncState` (first load), form `setError` (field), `ErrorZone` / `RouteError` (render bug) | shows an error on screen |
| Log | `src/lib/report-error.ts` (`reportError`) | calls `console.error` or telemetry |

The complete code for every module is in
[`references/error-handling.md`](references/error-handling.md). Load it before writing
or reviewing any error path.

## The error model

`AppError` carries `kind`, `code`, `status`, `userMessage`, `retryable` and the
original `cause`. Kinds: `network`, `throttled`, `forbidden`, `notFound`,
`duplicate`, `conflict`, `business`, `unknown`.

- **Classify by code, never by message text.** `toAppError` extracts the Dataverse
  error code (hex `0x8004…` or its decimal form) and the HTTP status, then maps
  them with a table (e.g. `0x80040237` / `0x80060892` → `duplicate`, `0x80040217` →
  `notFound`, `0x80040220` → `forbidden`, `0x80060882` → `conflict`, `0x80040265`
  → `business`). Regexes on words such as `already`, `in progress` or `duplicate`
  break with the next platform wording or language.
- **`userMessage` is never technical.** Only a `business` error (a plug-in or Custom
  API `InvalidPluginExecutionException`, written for users) shows the server text.
  Every other kind shows a fixed, actionable sentence; the raw message goes to the log.
- **`retryable`** is true for `network` and `throttled` only. The query `retry`
  option reads it; mutations are never retried automatically.

## Services: one result module, no local error code

- Every service calls Dataverse or a connector through `run` / `runPage` /
  `runOrNull` from `services/dataverse-result.ts`. No service defines its own
  `toError`, `unwrap`, `call` or `check`.
- **A service returns `null` only for a real "not found"** (`runOrNull`). A network
  failure or a missing privilege must never be displayed as "item not found".
- A feature-specific error (e.g. "a folder with this name exists") is derived from
  the kind at the call site (`kind === "duplicate"`), not by a new error class per service.

## Channels: each error reaches the user exactly once

| Situation | Channel | Mechanism |
|---|---|---|
| First load of a query fails | Inline, where the data would be | `AsyncState` (`ppbp-codeapps-components`) |
| Background refresh fails while data is shown | Toast | `QueryCache.onError` when `query.state.data !== undefined` |
| A write fails | Toast | `MutationCache.onError`, text from `meta.errorMessage` or `userMessage` |
| A write fails on a field the user can fix | The field | Mutation `meta: { silent: true }` + `form.setError` |
| A render or loader throws | Boundary | Route `errorElement` → `RouteError`; independent areas → `ErrorZone` |

- Mutation hooks contain **no** `toast.error` and no `try/catch`; per-mutation wording
  goes in `meta.errorMessage`.
- The default messages live in one table in `lib/errors.ts`, so wording and
  translation change in one place.

## Logging

- `reportError(appError, context)` is the only logging call. It defaults to the
  console and is pointed at the app's telemetry once at start-up (`setErrorSink`).
- The global channels and boundaries already report. Components never log.
- Log the real cause with context (query key, mutation key, boundary name). Showing
  a generic sentence to the user is correct. Losing the cause in the logs is not.

## Common issue: errors shown twice or never

Wiring a toast in `QueryCache.onError` for *every* failure doubles the inline error
on first load, while wiring nothing leaves background failures invisible. Toast only
when data is already displayed, and let `AsyncState` own the first load. The full
configuration is in [`references/error-handling.md`](references/error-handling.md) §4.

## Anti-patterns (DO NOT DO)

| Anti-pattern | Correct approach |
|---|---|
| **`catch { return null }` in a service.** A network or privilege failure becomes "not found". | `runOrNull` — `null` for `notFound` only, every other error propagates. |
| **`toError` / `unwrap` / `call` copied into each service.** | One `services/dataverse-result.ts`, imported by every service. |
| **Classifying with a regex on the message text** (`/already\|in progress/`). | `toAppError(error).kind`, classified from the Dataverse code and HTTP status. |
| **`toast.error(errorMessage(e))` repeated in every mutation**, helper redefined per feature. | `MutationCache.onError` + `meta.errorMessage` / `meta.silent`. |
| **`mutateAsync` + `try/catch` to show an error.** | `mutate(vars, { onError })` for local reactions; the toast stays global. |
| **Raw `error.message` in a table, dialog or toast.** | `userMessageOf(error)` / `appError.userMessage`. |
| **Replacing the real cause with a generic text everywhere.** | Generic text for the user; the real cause goes to `reportError`. |
| **Stray `console.error` in components or error pages.** | `reportError` — the single sink. |
| **Only route-level `errorElement`s.** One broken widget blanks the page. | `RouteError` on routes + `ErrorZone` around independent areas. |
| **Retrying every failure** (or a mutation). | `retry` driven by `retryable`; writes never retried automatically. |

## Skill boundaries

- Domain orientation and repository layout → `ppbp-codeapps-overview`
- Where services, hooks and components sit (layers) → `ppbp-codeapps-architecture`
- The `AsyncState` / `DataTable` components that render first-load errors and empty states → `ppbp-codeapps-components`
- Query keys, mutations, cache policy, FetchXML and Custom API calls → `ppbp-codeapps-data`
- Throwing a business error from a plug-in or Custom API → `ppbp-dv-custom-api`
- Generated services and the `IOperationResult` contract → `code-apps-preview:add-dataverse` and the other `add-*` skills
