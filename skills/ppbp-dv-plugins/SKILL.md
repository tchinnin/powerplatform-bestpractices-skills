---
name: ppbp-dv-plugins
description: >
  Use when the user is writing, registering, or debugging a Dataverse plug-in
  (IPlugin, pre/post-image, synchronous/asynchronous steps) or a Custom API
  (Request/Response parameters, bound/unbound actions).
license: MIT
metadata:
  author: powerplatform-bestpractices
  version: "1.0"
---

## Best practices

1. **Target .NET Framework 4.6.2** for on-premises compatibility and **net8.0** for isolated (sandbox) plug-ins on the cloud — choose at project creation, not after.
2. **Implement `IPlugin` directly**; do not inherit from a base class — Dataverse instantiates plug-ins per call and caches them; base class state is dangerous.
3. **Retrieve only the columns you need** in pre/post images and in explicit `Retrieve` calls — never use `ColumnSet(true)`; it ignores column security and wastes bandwidth.
4. **Use the service factory pattern**: resolve `IOrganizationService` once per execution from `serviceFactory.CreateOrganizationService(context.UserId)` so the call runs under the triggering user's security context.
5. **Register Custom APIs instead of custom messages** for new extensibility points — Custom APIs are first-class, discoverable, and callable from Power Automate and client SDKs.
6. **Always set `FullyQualifiedWebApiName`** on Custom API request/response parameters — it controls how they appear in the Web API and Power Automate.
7. **Throw `InvalidPluginExecutionException`** (not generic exceptions) to surface user-facing errors; use `OperationStatus.Failed` only for business rule failures.
8. **Register steps with the most restrictive image** — use Pre-Image only when you need pre-update values; avoid Post-Image on synchronous steps (performance cost).

## Common pitfalls

**Storing state in instance fields** — Dataverse reuses plug-in instances across calls; instance fields accumulate state from previous executions. *Declare all working variables inside `Execute()`.*

**Calling the organisation service in `PreValidation`** — The transaction has not started at `PreValidation`; service calls create a nested transaction and can cause deadlocks. *Move data access to `PreOperation` or `PostOperation`.*

**Missing plug-in registration update after schema changes** — If you add a column to the target table and your step uses an explicit image with a fixed column set, the new column is not included. *Update the image's attribute list in the Plugin Registration Tool.*

**Unbound Custom API vs. bound Custom API confusion** — Bound APIs require an entity type and a primary record; unbound APIs do not. Choosing the wrong type breaks the Web API path. *Unbound for global operations, bound for record-scoped operations.*

**Catching all exceptions silently** — Swallowing exceptions hides failures in asynchronous steps where no UI feedback exists. *Log to the Dataverse trace log (`ITracingService`) and re-throw or throw `InvalidPluginExecutionException`.*
