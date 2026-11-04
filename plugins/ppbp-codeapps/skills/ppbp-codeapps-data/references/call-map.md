# Dataverse call map — `docs/<app-name>/dataverse-calls.md`

Every Code App keeps an exhaustive inventory of what it reads and writes in
Dataverse, screen by screen and action by action. It is the document a reviewer
reads to judge the app's load on Dataverse, and the place where every deviation
from "one bounded, server-filtered call" is justified.

- **Location:** `docs/<app-name>/dataverse-calls.md`, at the repository root (see
  `ppbp-codeapps-overview` → Repository layout). Other app documentation may sit
  next to it in `docs/<app-name>/`.
- **Updated in the same change** as any new or modified call (service function,
  query, mutation, FetchXML, Custom API).
- **Describes what and why, not the code.** Query details live in the code; the map
  says which table, which scope, which channel, how often.

## Template

Copy this skeleton and fill it in. Keep the codes stable: reviews and commits refer
to them.

````markdown
# <App name> — Dataverse calls

## 1. Principles

- Filters, sorting, paging and counts are applied by Dataverse, never in the browser.
- Channels: native generated services (OData) first; FetchXML through the Dataverse
  connector when OData can't express the query; Custom APIs for multi-row or
  rule-guarded writes.
- All calls go through TanStack Query. Cache policy in §4.

## 2. Calls

| Code | Call | Table | Scope (rows, columns) | Channel | Cache (`staleTime`) |
|---|---|---|---|---|---|
| `R-ORDERS-PAGE` | Orders list page | `cr123_order` | 50 rows per page, 6 columns, filtered by status / country / search | FetchXML (connector), paging cookie | 30 s |
| `R-ORDERS-COUNT` | Orders counter | `cr123_order` | 1 number, same criteria as `R-ORDERS-PAGE` | FetchXML aggregate (connector) | 30 s |
| `R-COUNTRIES` | Country reference | `cr123_country` | whole table (< 300 rows), 3 columns | Native `getAll` | ∞ |
| `W-ORDER-STATUS` | Change an order status | `cr123_order` | 1 row | Native `update` (returns the row) | patches list cache |
| `A-ORDER-CLOSE` | Close an order and its lines | `cr123_order` (+ lines) | 1 order, N lines, 1 transaction | Custom API `cr123_CloseOrder` (bound) | invalidates `orders.lists` |

Prefixes: `R-` read, `W-` write, `A-` Custom API / action.

## 3. By screen and action

### Orders screen

| User action | Calls | Calls per action |
|---|---|---|
| Open the screen | `R-ORDERS-PAGE` (page 1, with count), `R-COUNTRIES` (cached) | 1–2 |
| Change a filter | `R-ORDERS-PAGE` (page 1), `R-ORDERS-COUNT` (debounced) | 2 |
| Scroll to the end | `R-ORDERS-PAGE` (next page) | 1 |
| Change a status | `W-ORDER-STATUS` | 1 |
| Close an order | `A-ORDER-CLOSE` | 1 |

## 4. Cache rules

| Data | `staleTime` | Consequence |
|---|---|---|
| Reference data | ∞ | 1 call per session while observed |
| Lists | 30 s | Refetch on return after 30 s; only page 1 kept when hidden |
| Default | 5 min | — |

## 5. Justified exceptions

| Code | Exception | Reason |
|---|---|---|
| `R-ORDERS-PAGE` | 2 calls per page (ids, then detail with `$expand`) | Nested collection `$expand` breaks paging (`Paging Cookie And Query Do Not Match`) |
````

## Review checks against the map

- Every service function and every query / mutation key in the code has a row.
- No row with "whole table" unless the table is a small reference table.
- No action costs more calls than its row says; no per-row call (N+1).
- Every "2 calls" or browser-side loop has a line in §5 — or is a finding.
