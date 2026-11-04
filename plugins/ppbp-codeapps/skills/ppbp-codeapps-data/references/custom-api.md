# Custom APIs from a Code App

A Custom API moves a precise piece of processing **into Dataverse**: it runs next
to the data, in one transaction, under the platform's security, and every client
(Code App, Power Automate, model-driven app) calls the same contract. In a Code App,
**propose one** whenever the browser would otherwise orchestrate many calls or own a
business rule that must hold.

Design (bound vs unbound, parameters, plug-in class, `InvalidPluginExecutionException`)
is owned by `ppbp-dv-custom-api`. This file covers the decision and the client side.

## 1. When to propose a Custom API

| Signal in the Code App | Why the browser is the wrong place | Custom API |
|---|---|---|
| N updates / creates sent from the browser for one user action ("apply to all colours", "close all lines") | Partial failure leaves data half-updated; N round-trips; throttling | **Bound** to the parent record if the scope is one record, else **unbound**; plug-in uses `UpdateMultiple` / `CreateMultiple` in **one transaction** |
| A business rule checked in a component or hook before writing | Bypassed by any other client; races between users | Bound/unbound action that validates and writes; throws `InvalidPluginExecutionException` with a user-facing message |
| An aggregate the UI computes from several queries | Many calls, data transferred only to be summed | Unbound function returning the figure (when FetchXML `aggregate` can't express it) |
| Find-then-create on a natural key | Two users create the duplicate at the same time | Action that upserts on the alternate key server-side (or alternate key + `duplicate` handling, see SKILL.md) |
| Writes that need privileges the user doesn't have | Can't be done safely from the client | Action whose plug-in runs with the required context |
| Same logic needed by a flow and the app | Duplicated logic drifts | One Custom API, called by both |

Rule of thumb: **if one user intent produces more than one write, or a write guarded
by a rule, propose a Custom API.** Present it to the user as a proposal (name,
bound/unbound, parameters, transaction scope); its creation follows the
`ppbp-dataverse-plugins` conventions.

## 2. Calling it — two channels

| Channel | Use when | Typing |
|---|---|---|
| **Native `dataverse-api` data source** — a typed service generated per action / function | Default | Typed parameters and response; functions (GET) and actions (POST) |
| **Dataverse connector** `PerformBoundAction[WithOrganization]` / `PerformUnboundAction[WithOrganization]` | The app already uses the connector and the native channel isn't available for this API | Untyped; **actions only** — the connector has no GET path for functions |

How to generate the native typed service is shown in Microsoft's sample
`microsoft/PowerAppsCodeApps/samples/Dataverse` (README, "Dataverse Functions &
Actions"); the connector variant in `samples/DataverseConnector`. Follow the official
`code-apps-preview` procedure for adding any data source.

Either way, the call goes through `services/` + `run` (from `services/dataverse-result.ts`)
and is consumed through `useMutation` (actions) or `useQuery` (functions).

## 3. Native typed service — wrapper and mutation

Assume an unbound action `cr123_ApplyFabricToColors` generated as
`src/generated/services/Cr123_ApplyFabricToColorsService.ts`. The generated method
name and parameter order are owned by the generator: `grep` them before writing
the wrapper.

```ts
// src/services/fabrics.service.ts (excerpt)
import { Cr123_ApplyFabricToColorsService } from "@/generated/services/Cr123_ApplyFabricToColorsService";
import { run } from "./dataverse-result";

export const fabricsService = {
  // One server transaction: all colours are updated, or none.
  async applyFabricToColors(fabricId: string, fabricCode: string): Promise<void> {
    await run(() => Cr123_ApplyFabricToColorsService.cr123_ApplyFabricToColors(fabricId, fabricCode));
  },
};
```

```ts
// src/components/fabrics/fabrics.queries.ts (excerpt)
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { fabricsService } from "@/services/fabrics.service";

export const fabricKeys = {
  all: ["fabrics"] as const,
  lists: () => [...fabricKeys.all, "list"] as const,
  mutations: {
    applyToColors: () => [...fabricKeys.all, "apply-to-colors"] as const,
  },
};

export function useApplyFabricToColors() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationKey: fabricKeys.mutations.applyToColors(),
    mutationFn: ({ fabricId, fabricCode }: { fabricId: string; fabricCode: string }) =>
      fabricsService.applyFabricToColors(fabricId, fabricCode),
    meta: { errorMessage: "The fabric could not be applied to its colours." },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: fabricKeys.lists() }),
  });
}
```

A `business` error thrown by the plug-in reaches the user with its own message
through the global `MutationCache` channel (`ppbp-codeapps-errors`).

## 4. Connector channel — bound and unbound actions

```ts
// src/services/dataverse-actions.ts
import { getContext } from "@microsoft/power-apps/app";
import { MicrosoftDataverseService } from "@/generated/services/MicrosoftDataverseService";
import { toAppError } from "@/lib/errors";
import { run } from "./dataverse-result";

export type ActionResponse = Record<string, unknown>;

let orgUrl: Promise<string> | undefined;

function organization(): Promise<string> {
  orgUrl ??= getContext().then((context) => {
    const url = context.app.dataverseOrgUrl;
    if (!url) throw toAppError("The Dataverse organization URL is not available from the host.");
    return url;
  });
  return orgUrl;
}

// POST {entitySet}({id})/Microsoft.Dynamics.CRM.{uniqueName}
export async function performBoundAction(
  entitySetName: string,
  uniqueName: string,
  recordId: string,
  parameters: Record<string, unknown>,
): Promise<ActionResponse> {
  const org = await organization();
  return run(() =>
    MicrosoftDataverseService.PerformBoundActionWithOrganization(
      org,
      entitySetName,
      `Microsoft.Dynamics.CRM.${uniqueName}`,
      recordId,
      parameters,
    ),
  );
}

// POST /{uniqueName}
export async function performUnboundAction(
  uniqueName: string,
  parameters: Record<string, unknown>,
): Promise<ActionResponse> {
  const org = await organization();
  return run(() => MicrosoftDataverseService.PerformUnboundActionWithOrganization(org, uniqueName, parameters));
}
```

If the app also uses `services/dataverse-connector.ts` (FetchXML), share its
`organization()` helper instead of declaring a second one.

```ts
// src/services/orders.service.ts (excerpt) — a typed façade over the untyped call
import { performBoundAction } from "./dataverse-actions";

export type CloseOrderResult = { closedLines: number };

export const ordersActions = {
  async close(orderId: string, reason: string): Promise<CloseOrderResult> {
    const response = await performBoundAction("cr123_orders", "cr123_CloseOrder", orderId, { Reason: reason });
    return { closedLines: Number(response.ClosedLines ?? 0) };
  },
};
```

Parameter names (`Reason`, `ClosedLines`) are the Custom API's unique names — the
public contract fixed at creation (see `ppbp-dv-custom-api`).

## 5. Bounded concurrency — only for independent writes

When writes are genuinely independent (each one is meaningful on its own, a partial
result is acceptable and the user can retry the failures), the browser may send them
with a small concurrency limit. This is never a substitute for a transaction.

```ts
// src/lib/concurrency.ts
// Runs fn on each item with at most `limit` calls in flight. After a failure no new
// call starts; running calls finish, then the first error is rethrown.
export async function forEachConcurrent<T>(
  items: Iterable<T>,
  limit: number,
  fn: (item: T) => Promise<unknown>,
): Promise<void> {
  const iterator = items[Symbol.iterator]();
  let failed = false;
  const worker = async () => {
    for (let next = iterator.next(); !next.done && !failed; next = iterator.next()) {
      try {
        await fn(next.value);
      } catch (error) {
        failed = true;
        throw error;
      }
    }
  };
  const results = await Promise.allSettled(Array.from({ length: Math.max(1, limit) }, worker));
  const rejected = results.find((r): r is PromiseRejectedResult => r.status === "rejected");
  if (rejected) throw rejected.reason;
}
```

## Wrong / correct

| Wrong | Correct |
|---|---|
| `await Promise.all(ids.map((id) => service.update(id, patch)))` for one user action | Custom API with `UpdateMultiple` in one transaction |
| Same, with a concurrency limit, for data that must stay consistent | Custom API — a limit doesn't make it atomic |
| Business rule checked in the page before calling `update` | Rule enforced in the Custom API / plug-in; the UI only pre-validates for UX |
| `fetch('/api/data/v9.2/cr123_CloseOrder', …)` | Generated `dataverse-api` service or connector action, via `services/` + `run` |
| Calling a Dataverse **function** through `PerformUnboundAction` | Native typed service (the connector has no GET path) |
| Untyped action response passed to components | Typed façade in `services/` |
