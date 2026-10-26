---
name: ppbp-dv-custom-api
description: >
  Dataverse Custom API design and implementation best practices. Use when the user is
  creating a Custom API (bound vs. unbound choice, request/response parameters,
  parameter unique names), implementing the Custom API plug-in class, calling a Custom
  API from Power Automate or client SDKs, or resolving security roles by ParentRootRoleId.
  Also use when the user asks about Custom API vs. custom messages or InvalidPluginExecutionException.
license: MIT
user-invocable: true
model: sonnet
allowed-tools: Read, Bash, Grep, Glob, WebSearch
metadata:
  author: powerplatform-bestpractices
  version: "1.2.0"
---

## Official skill

No official Microsoft skill exists for this topic. Custom API authoring is not covered by any official skill in the `dataverse:*` namespace.

## Custom API vs. custom messages

**Always register Custom APIs instead of custom messages** for new extensibility points. Custom APIs are first-class Dataverse objects: they appear in the Web API metadata, are discoverable from Power Automate, and support typed request/response parameters. Custom messages are a legacy mechanism with none of these properties.

## Bound vs. unbound

| Type | When to use | Web API path |
|---|---|---|
| **Unbound** | Global operations — not scoped to a specific record | `POST /api/data/v9.2/<ApiUniqueName>` |
| **Bound** | Record-scoped operations — require an entity record as input | `POST /api/data/v9.2/<EntitySet>(<id>)/Microsoft.Dynamics.CRM.<ApiUniqueName>` |

Choosing the wrong type breaks the Web API path and makes the action uncallable from Power Automate without a workaround.

## Fixed-at-creation choices

Binding, bound table, function/action, allowed steps, and a parameter's unique name, type and optional flag are **fixed at creation**: changing one later means deleting and recreating the Custom API or the parameter. Decide them before the first registration, and create the Custom API in the dev unmanaged solution.

## Request and response parameters

1. **Choose each parameter's unique name as the public contract.** The unique name is the name callers use in the Web API and in Power Automate, and it can't be changed after creation. Use clear PascalCase English names.
2. **Keep parameter types simple** — use scalar types (string, int, bool, EntityReference) where possible; complex types require OData annotations that many callers cannot parse.
3. **Mark parameters as optional when they have a sensible default** — required parameters block callers who don't need them. Decide before creation: `optional` is fixed once created.

## Custom API plug-in class

The plug-in class registered against a Custom API follows the same rules as a step plugin (see `ppbp-dv-step-plugin` for build and context patterns), with one addition:

- **Throw `InvalidPluginExecutionException`** with `OperationStatus.Failed` for business rule failures that must surface as a structured error to the caller. Do not throw generic exceptions — callers receive an opaque 500 without diagnostic information.

## Security role resolution

When a Custom API needs to resolve a security role programmatically (e.g., to assign it to a team or user), **never query by display name**. Every Business Unit has its own copy of each role with the same display name; querying by name returns all copies with no deterministic result.

**Query by `ParentRootRoleId` filtered to the target Business Unit:**

| | Wrong | Correct |
|---|---|---|
| Query filter | `name == "My Role"` | `parentrootroleid == rootRoleId AND businessunitid == targetBuId` |

```csharp
// Wrong — returns every BU's copy of the role
var wrong = service.RetrieveMultiple(new QueryExpression("role")
{
    ColumnSet = new ColumnSet("roleid"),
    Criteria = { Conditions = { new ConditionExpression("name", ConditionOperator.Equal, roleName) } }
});

// Correct — returns exactly the BU-specific instance
var correct = service.RetrieveMultiple(new QueryExpression("role")
{
    ColumnSet = new ColumnSet("roleid"),
    Criteria =
    {
        Conditions =
        {
            new ConditionExpression("parentrootroleid", ConditionOperator.Equal, rootRoleId),
            new ConditionExpression("businessunitid",   ConditionOperator.Equal, targetBuId)
        }
    }
});
var roleId = correct.Entities.Single().Id;
```

## Anti-patterns (DO NOT DO)

| Anti-pattern | Correct approach |
|---|---|
| Custom message instead of Custom API — Not discoverable, no typed parameters, not callable from Power Automate. | Always use Custom API for new extensibility points. |
| Unbound Custom API for record-scoped operations (or bound for global) — Wrong type breaks the Web API path. | Unbound for global operations, bound for record-scoped operations. |
| Renaming or retyping a parameter after release — unique name, type and optional flag are fixed at creation, and callers depend on them. | Add a new parameter (optional) or a new Custom API, and migrate callers. |
| Throwing generic exceptions — Callers receive an opaque 500 with no diagnostic information. | Throw `InvalidPluginExecutionException` with `OperationStatus.Failed` for business rule failures. |
| Resolving security roles by display name across Business Units — Returns all BU copies with no deterministic result. | Query by `ParentRootRoleId` filtered to the target BU — see example above. |

## Skill boundaries

This skill covers Custom API design and implementation. It does not cover:

- Domain orientation and repository layout → `ppbp-dv-plugins-overview`
- Registration procedure for the Custom API and its plug-in → `dataverse:dv-overview`
- Project scaffolding, build → `ppbp-dv-plugin-build`
- Step plugin implementation, execution pipeline, images → `ppbp-dv-step-plugin`
- Dataverse schema design → `ppbp-dv-tables`, `ppbp-dv-columns`
- Power Automate cloud flows → out of scope for this plugin
