---
name: ppbp-dv-plugin-build
description: >
  Dataverse plug-in project scaffolding, build, and deployment. Use when the user is
  initialising a plug-in project (pac plugin init), generating early-bound classes
  (pac modelbuilder build), bumping assembly version, running a release build
  (dotnet clean + dotnet build), or deploying with pac plugin push. Also use when
  the user asks about .snk files, NuGet metadata, or the Plugin Registration Tool
  for first-time deployment.
license: MIT
metadata:
  author: powerplatform-bestpractices
  version: "1.2.0"
---

## Official skill

No official Microsoft skill exists for this topic. Dataverse plug-in authoring (IPlugin, Custom APIs, PAC CLI plugin workflow) is not covered by any official skill in the `dataverse:*` namespace.

## Best practices

1. **Target .NET Framework 4.6.2** for on-premises compatibility and **net8.0** for isolated (sandbox) plug-ins on the cloud — choose at project creation, not after.
2. **Always scaffold with `pac plugin init`** — it generates `PluginBase.cs`, the strong-name key (`.snk`), and the correct `.csproj` NuGet package configuration.
3. **Increment `AssemblyVersion` and `FileVersion` in `.csproj` before every deployment** — Dataverse uses the version to detect assembly changes; deploying without a version bump silently skips the update.
4. **Deploy the NuGet package (`.nupkg`), never the raw `.dll`.** `pac plugin push` defaults to `--type Nuget`; pushing the bare assembly bypasses the plug-in package model the project is built around. Always point `--pluginFile` at the generated `.nupkg`.
5. **Never hand-edit the generated early-bound classes** in `Models/` — they are build output; regenerate with `pac modelbuilder build` when the schema changes (see `ppbp-dv-plugins-overview`).

## PAC CLI workflow

### 1 — Scaffold the project

```sh
pac plugin init --outputDirectory <ProjectName> --author "<Author>"
```

Generates: `PluginBase.cs`, `<ProjectName>.snk`, `<ProjectName>.csproj`, sample plugin file.  
After init: set `<RootNamespace>`, update NuGet metadata (Company, Description), leave `<PluginId>` empty until first deployment.

### 2 — Generate early-bound classes

```sh
pac modelbuilder build \
  --outdirectory <ProjectName>/Models \
  --namespace <Company>.<Product>.Models \
  --environment https://<org>.crm.dynamics.com/ \
  --emitfieldsclasses \
  --generateGlobalOptionSets \
  --entitynamesfilter "table1;table2;table3"
```

Do **not** add `--generatesdkmessages` — it floods the project with SDK message classes that are not needed.

The generated `Models/` are **build output — never hand-edit them**. When the schema changes, re-run this command to regenerate; manual edits are lost on the next run and diverge from the live schema.

### 3 — Increment version before every build

In `.csproj`, bump both fields:

```xml
<AssemblyVersion>1.0.1.0</AssemblyVersion>
<FileVersion>1.0.1.0</FileVersion>
```

Use **Major.Minor.Patch.Build**: Patch for bug fixes, Minor for new features, Major for breaking changes.

### 4 — Release build

```sh
dotnet clean && dotnet build -c Release
```

`dotnet clean` is mandatory — without it the NuGet package is not regenerated and the version bump is silently ignored.

Output: `bin/Release/net462/<ProjectName>.dll` and `bin/Release/<ProjectName>.<Version>.nupkg`. **Deploy the `.nupkg`** — the `.dll` is just an intermediate artifact.

### 5 — Deploy

**First deployment** — `pac plugin push` requires an existing plugin GUID. Register the assembly once via the Plugin Registration Tool, then store the returned GUID in `.csproj`:

```xml
<PluginId>xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx</PluginId>
```

**Subsequent deployments** — read the GUID from `.csproj` and push:

```sh
PLUGIN_ID=$(dotnet msbuild <ProjectName>.csproj -getProperty:PluginId -nologo)
pac plugin push --pluginId "$PLUGIN_ID" --pluginFile ./bin/Release/<ProjectName>.<Version>.nupkg
```

For the **dev inner loop**, push the assembly by `--pluginId` rather than `--solution-name` — direct-by-GUID is faster and avoids a solution dependency on every iteration. For **cross-environment promotion**, the assembly must still ship inside a solution exported/imported via the official `dataverse:dv-solution` skill — that is the ALM path, not a per-iteration push.

## Common issue: dotnet clean and version bumps

Skipping `dotnet clean` before a release build silently deploys the old assembly even when `.csproj` has been updated with a new version number — the NuGet package is not regenerated. Always run `dotnet clean && dotnet build -c Release`.

## Common issue: First deployment requires the Plugin Registration Tool

`pac plugin push --pluginId` requires a GUID that only exists after the assembly has been registered at least once. There is no CLI-only path for the initial registration — the Plugin Registration Tool (available via NuGet: `Microsoft.CrmSdk.XrmTooling.PluginRegistrationTool`) must be used once to create the record and obtain the GUID, which is then stored in `<PluginId>` in `.csproj` for all subsequent deployments.

## Anti-patterns (DO NOT DO)

| Anti-pattern | Correct approach |
|---|---|
| Using `--solution-name` for the dev inner loop — adds a solution dependency and is slower on every iteration. | For iteration, store the plugin GUID in `<PluginId>` and use `pac plugin push --pluginId ... --pluginFile ...`. For promotion, ship the assembly in a solution via `dataverse:dv-solution`. |
| Skipping `dotnet clean` before a release build — The NuGet package is not regenerated; a version bump in `.csproj` is silently ignored. | Always run `dotnet clean && dotnet build -c Release`. |
| Creating plugin projects by hand without `pac plugin init` — Misses PluginBase, .snk, and correct NuGet config. | Always scaffold with `pac plugin init`. |
| Pushing the raw `.dll` (`--type Assembly`) — bypasses the plug-in package model the project is built around. | Push the generated `.nupkg`; `pac plugin push` uses `--type Nuget` by default. |
| Hand-editing a generated early-bound class in `Models/` — lost on the next regeneration and diverges from the live schema. | Never edit generated classes; re-run `pac modelbuilder build` to regenerate. |

## Skill boundaries

This skill covers plug-in project scaffolding, build, and deployment. It does not cover:

- Domain orientation and repository layout → `ppbp-dv-plugins-overview`
- Step plugin implementation, execution pipeline, images → `ppbp-dv-step-plugin`
- Custom API design and implementation → `ppbp-dv-custom-api`
- Solution packaging, export/import (the authority for shipping the assembly) → `dataverse:dv-solution`, `ppbp-alm-solutions`
