# FetchXML through the Dataverse connector

Use this when the native generated service (OData `select / filter / orderBy / top`)
cannot express the query **on the server**: aggregates and counts beyond a simple
filter, `distinct`, `link-entity` with conditions, `exists` / `not exists` on related
tables, filters on a collection reached through a lookup, or `$expand`.

## Why the connector

The native Dataverse client of a Code App has no `fetchXml` parameter and no
`$expand`. Both are available through the **Microsoft Dataverse connector**
(`shared_commondataserviceforapps`), whose generated `MicrosoftDataverseService`
exposes `ListRecordsWithOrganization(..., fetchXml)`. Microsoft's sample
`microsoft/PowerAppsCodeApps/samples/DataverseConnector` documents how to add it and
how it differs from native Dataverse. Note: the official `add-connector` skill
redirects the legacy `commondataservice` connector to `add-dataverse` (native); the
connector you need here is `shared_commondataserviceforapps`, added as a connector
data source, alongside the native tables.

Keep both: **native** generated services for typed CRUD and simple lists, the
**connector** for FetchXML, `$expand` and actions. Writes stay on the native services.

## 1. Connector wrapper — one module, no React

```ts
// src/services/dataverse-connector.ts
import { getContext } from "@microsoft/power-apps/app";
import { MicrosoftDataverseService } from "@/generated/services/MicrosoftDataverseService";
import { toAppError } from "@/lib/errors";
import { run } from "./dataverse-result";

export type DataverseRow = Record<string, unknown>;
export type FetchPage = { rows: DataverseRow[]; pagingCookie?: string; moreRecords: boolean };

// Formatted values (choice labels, lookup names) come back as annotations.
const PREFER = 'odata.include-annotations="*"';
const ACCEPT = "application/json";

// The annotation is an XML element; its pagingcookie attribute is URL-encoded twice.
function nextPagingCookie(annotation: unknown): string | undefined {
  if (typeof annotation !== "string") return undefined;
  const match = /pagingcookie="([^"]*)"/.exec(annotation);
  return match ? decodeURIComponent(decodeURIComponent(match[1])) : undefined;
}

let orgUrl: Promise<string> | undefined;

function organization(): Promise<string> {
  orgUrl ??= getContext().then((context) => {
    const url = context.app.dataverseOrgUrl;
    if (!url) throw toAppError("The Dataverse organization URL is not available from the host.");
    return url;
  });
  return orgUrl;
}

export async function fetchXmlPage(entitySetName: string, fetchXml: string): Promise<FetchPage> {
  const org = await organization();
  const body = await run(() =>
    MicrosoftDataverseService.ListRecordsWithOrganization(
      org,
      entitySetName,
      PREFER,
      ACCEPT,
      undefined, // x-ms-odata-metadata-full
      undefined, // MSCRM.IncludeMipSensitivityLabel
      undefined, // $select
      undefined, // $filter
      undefined, // $orderby
      undefined, // $expand
      fetchXml,
    ),
  );
  const rows = (body.value as DataverseRow[] | undefined) ?? [];
  return {
    rows,
    pagingCookie: nextPagingCookie(body["@Microsoft.Dynamics.CRM.fetchxmlpagingcookie"]),
    moreRecords: body["@Microsoft.Dynamics.CRM.morerecords"] === true,
  };
}

export type ODataQuery = { select: string; filter: string; orderby?: string; expand?: string };

// OData with $expand — bounded reads only (e.g. the detail of the ids of one page).
export async function listWithExpand(entitySetName: string, query: ODataQuery): Promise<DataverseRow[]> {
  const org = await organization();
  const body = await run(() =>
    MicrosoftDataverseService.ListRecordsWithOrganization(
      org,
      entitySetName,
      PREFER,
      ACCEPT,
      undefined,
      undefined,
      query.select,
      query.filter,
      query.orderby,
      query.expand,
    ),
  );
  return (body.value as DataverseRow[] | undefined) ?? [];
}
```

The connector is untyped. Map every row to a typed UI model in a pure mapper
(`<feature>.mappers.ts`) right after the call; nothing untyped leaves the service.

## 2. Builders — escape everything, build criteria once

```ts
// src/lib/fetchxml.ts
export function xmlEscape(value: string): string {
  return value
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&apos;");
}

// "contains" for operator="like": escape the LIKE wildcards % _ [ , then XML.
export function likeContains(term: string): string {
  return xmlEscape(`%${term.replace(/[%_[]/g, "[$&]")}%`);
}

export function likeCondition(attribute: string, term: string): string {
  return `<condition attribute="${attribute}" operator="like" value="${likeContains(term)}" />`;
}

export function condition(attribute: string, operator: string, value?: string): string {
  return value === undefined
    ? `<condition attribute="${attribute}" operator="${operator}" />`
    : `<condition attribute="${attribute}" operator="${operator}" value="${xmlEscape(value)}" />`;
}

export function inCondition(attribute: string, values: readonly string[]): string {
  if (values.length === 0) return "";
  const items = values.map((v) => `<value>${xmlEscape(v)}</value>`).join("");
  return `<condition attribute="${attribute}" operator="in">${items}</condition>`;
}

export function attributes(names: readonly string[]): string {
  return names.map((name) => `<attribute name="${name}" />`).join("");
}
```

```ts
// src/services/orders.fetchxml.ts — one criteria builder shared by the page and the count
import { attributes, condition, inCondition, likeCondition, xmlEscape } from "@/lib/fetchxml";

export type OrderFilters = { search: string; statuses: number[]; countryIds: string[] };

export const ORDERS_PAGE_SIZE = 50;
const LIST_COLUMNS = ["cr123_orderid", "cr123_number", "cr123_status", "cr123_amount"];

function criteria({ search, statuses, countryIds }: OrderFilters): string {
  const term = search.trim();
  const filters =
    `<filter type="and">` +
    condition("statecode", "eq", "0") +
    (term ? likeCondition("cr123_number", term) : "") +
    inCondition("cr123_status", statuses.map(String)) +
    `</filter>`;
  // exists = SQL EXISTS: filters on a related collection without duplicating rows.
  const byCountry =
    countryIds.length === 0
      ? ""
      : `<link-entity name="cr123_ordercountry" from="cr123_orderid" to="cr123_orderid" link-type="exists">` +
        `<filter>${inCondition("cr123_countryid", countryIds)}</filter>` +
        `</link-entity>`;
  return filters + byCountry;
}

export function orderPageFetchXml(filters: OrderFilters, page: number, pagingCookie?: string): string {
  const cookie = pagingCookie ? ` paging-cookie="${xmlEscape(pagingCookie)}"` : "";
  return (
    `<fetch count="${ORDERS_PAGE_SIZE}" page="${page}"${cookie}>` +
    `<entity name="cr123_order">` +
    attributes(LIST_COLUMNS) +
    // a unique last sort column keeps paging stable
    `<order attribute="cr123_number" /><order attribute="cr123_orderid" />` +
    criteria(filters) +
    `</entity></fetch>`
  );
}

// Same criteria, aggregated on the server: one number comes back, not the rows.
export function orderCountFetchXml(filters: OrderFilters): string {
  return (
    `<fetch aggregate="true">` +
    `<entity name="cr123_order">` +
    `<attribute name="cr123_orderid" aggregate="countcolumn" distinct="true" alias="total" />` +
    criteria(filters) +
    `</entity></fetch>`
  );
}
```

Use paging cookies (`count` + `page` + `paging-cookie`) rather than simple paging
(`count` + `page` alone): simple paging re-reads every previous page on the server and
stops at 50,000 rows. Never combine `top` with paging.

## 3. Service + queries — paging with the cookie, count once per filter set

```ts
// src/services/orders.service.ts
import { fetchXmlPage } from "./dataverse-connector";
import { orderCountFetchXml, orderPageFetchXml, type OrderFilters } from "./orders.fetchxml";
import { toOrderRow, type OrderRow } from "./orders.mappers";

export type OrderPageParam = { page: number; pagingCookie?: string };
export type OrderPage = { items: OrderRow[]; next?: OrderPageParam };

export const ordersService = {
  async listPage(filters: OrderFilters, param: OrderPageParam): Promise<OrderPage> {
    const result = await fetchXmlPage("cr123_orders", orderPageFetchXml(filters, param.page, param.pagingCookie));
    return {
      items: result.rows.map(toOrderRow),
      next: result.moreRecords ? { page: param.page + 1, pagingCookie: result.pagingCookie } : undefined,
    };
  },

  async count(filters: OrderFilters): Promise<number> {
    const result = await fetchXmlPage("cr123_orders", orderCountFetchXml(filters));
    return Number(result.rows[0]?.total ?? 0);
  },
};
```

```ts
// src/services/orders.mappers.ts
import type { DataverseRow } from "./dataverse-connector";

export type OrderRow = { id: string; number: string; status: number; statusLabel: string; amount: number };

const FORMATTED = "@OData.Community.Display.V1.FormattedValue";

export function toOrderRow(row: DataverseRow): OrderRow {
  return {
    id: String(row.cr123_orderid),
    number: String(row.cr123_number ?? ""),
    status: Number(row.cr123_status),
    statusLabel: String(row[`cr123_status${FORMATTED}`] ?? ""),
    amount: Number(row.cr123_amount ?? 0),
  };
}
```

```ts
// src/components/orders/orders.queries.ts
import { infiniteQueryOptions, keepPreviousData, queryOptions, useInfiniteQuery, useQuery } from "@tanstack/react-query";
import { ordersService, type OrderPageParam } from "@/services/orders.service";
import type { OrderFilters } from "@/services/orders.fetchxml";

export const orderKeys = {
  all: ["orders"] as const,
  lists: () => [...orderKeys.all, "list"] as const,
  list: (filters: OrderFilters) => [...orderKeys.lists(), filters] as const,
  count: (filters: OrderFilters) => [...orderKeys.all, "count", filters] as const,
};

export const orderListOptions = (filters: OrderFilters) =>
  infiniteQueryOptions({
    queryKey: orderKeys.list(filters),
    queryFn: ({ pageParam }) => ordersService.listPage(filters, pageParam),
    initialPageParam: { page: 1 } as OrderPageParam,
    getNextPageParam: (last) => last.next,
    placeholderData: keepPreviousData,
    staleTime: 30_000,
    meta: { firstPageOnly: true },
  });

// Keyed on the same (debounced, normalised) filters as the list: one count per filter set.
export const orderCountOptions = (filters: OrderFilters) =>
  queryOptions({
    queryKey: orderKeys.count(filters),
    queryFn: () => ordersService.count(filters),
    placeholderData: keepPreviousData,
    staleTime: 30_000,
  });

export const useOrders = (filters: OrderFilters) => useInfiniteQuery(orderListOptions(filters));
export const useOrderCount = (filters: OrderFilters) => useQuery(orderCountOptions(filters));
```

Filters reach a key already normalised (trimmed search, sorted arrays) and committed
after debounce — the filters store holds only committed values
(`ppbp-codeapps-architecture` → `references/stores.md`) — so a keystroke never fires a
list call and a count call.

## 4. Counting — pick the cheapest exact answer

| Need | Use | Limit |
|---|---|---|
| "N results" next to a paged OData list | `count: true` on the **first page** of the native `getAll` (`result.count`) | Capped at 5,000 |
| Same, FetchXML list | `returntotalrecordcount="true"` on the first page (`@Microsoft.Dynamics.CRM.totalrecordcount`); not combinable with `top` | Capped at 5,000 |
| Exact count beyond 5,000, or count over joined criteria | `aggregate="true"` + `countcolumn` (§2), its own query keyed on the filters | Aggregate queries are limited to 50,000 rows |
| Sums, averages, group by | FetchXML `aggregate` + `groupby` | 50,000 |
| Anything heavier or reused by several apps | A Custom API (see `custom-api.md`) | — |

Never count by loading rows and reading `.length`.

## 5. One call per page — and when two are unavoidable

Aim for one call per page. Compute derived flags in the same FetchXML (a
`link-entity` with an alias, or an `exists` per flag) instead of a second "flags"
query per page.

A second call is justified only when the platform forces it. Example:
**nested `$expand` of collections breaks paging** — page 2 fails with
`Paging Cookie And Query Do Not Match`. Then:

1. Page the **ids** with FetchXML (`count` + `page` + criteria, ids only).
2. Read the **detail of those ids** in one bounded call with `$expand`
   (`Microsoft.Dynamics.CRM.In(PropertyName='cr123_orderid',PropertyValues=[…])`),
   both inside the same `queryFn`, and reorder the details by the ids' order.

Document the reason in `docs/<app-name>/dataverse-calls.md`.

## Wrong / correct

| Wrong | Correct |
|---|---|
| Native `getAll` for every page, then filter / join / count in JS | One FetchXML query with the criteria on the server |
| `link-type="inner"` on a one-to-many join to filter (duplicates rows, breaks paging) | `link-type="exists"` |
| `value="%${q}%"` built by hand | `likeContains(q)` — LIKE wildcards and XML escaped |
| `top="5000"` "to be safe" | `count` + `page` paging, or an aggregate |
| A count query fired on every keystroke | Count keyed on debounced, normalised filters, or returned with page 1 |
| A second "flags" call per page | `link-entity` / `exists` in the same FetchXML |
| Untyped connector rows passed to components | Mapped to a typed model in the service layer |
| Writes through the connector "because it is already there" | Native generated services for writes |
