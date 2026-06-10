---
name: ppbp-dv-step-plugin
description: >
  Dataverse step plugin implementation best practices. Use when the user is implementing
  an IPlugin step (Pre-Validation, Pre-Operation, Post-Operation), configuring pre/post
  images, choosing synchronous vs. asynchronous execution, selecting the correct execution
  pipeline stage, retrieving only required columns, or using the service factory pattern.
  Also use when the user asks about step registration, image attribute lists, or execution
  context access.
license: MIT
metadata:
  author: powerplatform-bestpractices
  version: "1.0.0"
---

## Official skill

No official Microsoft skill exists for this topic. Dataverse plug-in step implementation is not covered by any official skill in the `dataverse:*` namespace.

## Execution pipeline stages

| Stage | When | Service calls allowed | Use for |
|---|---|---|---|
| **Pre-Validation** | Before security checks | No — transaction not started | Input validation only; no DB access |
| **Pre-Operation** | After security, before DB write | Yes | Transform or enrich the message before it is committed |
| **Post-Operation** | After DB write | Yes | React to committed data; trigger side effects |

**Synchronous vs. asynchronous:**
- **Synchronous** — runs in the user's transaction; errors roll back the operation. Use for validation and data enrichment.
- **Asynchronous** — runs outside the transaction in the background. Use for notifications, integrations, or slow operations.

## Step implementation best practices

1. **Call the organisation service in `Pre-Operation` or `Post-Operation`**, never in `Pre-Validation` — the transaction has not started at that stage; service calls create a nested transaction and can cause deadlocks.
2. **Use the service factory pattern**: resolve `IOrganizationService` once per execution from `serviceFactory.CreateOrganizationService(context.UserId)` so the call runs under the triggering user's security context.
3. **Retrieve only the columns you need** in explicit `Retrieve` calls and in step images — never use `ColumnSet(true)`; it ignores column security and wastes bandwidth.
4. **Register steps with the most restrictive image** — use Pre-Image only when you need pre-update values; avoid Post-Image on synchronous steps (performance cost on every sync execution).
5. **Update the image's attribute list after every schema change** — if a step uses an explicit image with a fixed column set, new columns are silently excluded until the registration is updated.
6. **Throw `InvalidPluginExecutionException`** (not generic exceptions) to surface user-facing errors in synchronous steps; use `OperationStatus.Failed` only for business rule failures.
7. **Log to `ITracingService`** before rethrowing in asynchronous steps — async failures have no UI feedback; the trace log is the only debugging surface.

## Step registration checklist

Before registering a step:
- Choose the correct entity (logical name, lowercase).
- Choose the correct message (`Create`, `Update`, `Delete`, or custom).
- Choose the correct stage (`PreValidation`, `PreOperation`, `PostOperation`).
- Choose sync or async.
- Define the attribute filter for `Update` steps — omitting it triggers the step on every update, regardless of which columns changed.
- Define the minimum required image columns — avoid `ColumnSet(true)` in images.

## Anti-patterns (DO NOT DO)

| Anti-pattern | Correct approach |
|---|---|
| Calling the organisation service in `PreValidation` — The transaction has not started; service calls create a nested transaction and can cause deadlocks. | Move data access to `PreOperation` or `PostOperation`. |
| Missing plug-in registration update after schema changes — If a step uses an explicit image with a fixed column set, new columns are silently excluded. | Update the image's attribute list in the Plugin Registration Tool after every schema change that affects step images. |
| Catching all exceptions silently in async steps — Swallows failures where no UI feedback exists. | Log to `ITracingService` and re-throw, or throw `InvalidPluginExecutionException`. |
| Registering `Update` steps without an attribute filter — Fires on every update to the entity, even unrelated columns. | Define an explicit attribute filter listing only the columns that should trigger the step. |
| Post-Image on synchronous steps — The platform fetches Post-Image data synchronously, adding a read to every execution. | Use Post-Image only when the post-commit values are genuinely needed; prefer async for Post-Image consumers. |

## Skill boundaries

This skill covers step plugin implementation. It does not cover:

- Domain orientation and repository layout → `ppbp-dv-plugins-overview`
- Project scaffolding, build, deployment → `ppbp-dv-plugin-build`
- Custom API design and implementation → `ppbp-dv-custom-api`
- Dataverse schema design → `ppbp-dv-tables`, `ppbp-dv-columns`
