---
name: ppbp-dv-plugin-build
description: >
  Dataverse plug-in project scaffolding, versioning and release build. Use when the user
  is initialising a plug-in project (pac plugin init), generating early-bound classes
  (pac modelbuilder build), bumping the assembly version, or running a release build
  (dotnet clean + dotnet build) to produce the .nupkg. Also use when the user asks
  about signing, .snk files, or NuGet package metadata.
license: MIT
user-invocable: true
model: sonnet
allowed-tools: Read, Write, Edit, Bash, Grep, Glob, WebSearch
metadata:
  author: powerplatform-bestpractices
  version: "2.1.0"
---

## Official skill

No official Microsoft skill exists for plug-in project setup and build. Dataverse plug-in authoring (IPlugin, Custom APIs, the PAC CLI plug-in workflow) is not covered by any official skill in the `dataverse:*` namespace.

## Best practices

1. **Target .NET Framework 4.8 (`net48`) for every plug-in project.** Plug-ins run on .NET Framework in the Dataverse sandbox.
   - `net8.0` is only for **client-side** code that calls Dataverse through the SDK: console apps, Azure Functions, integration tools. Never use it for a plug-in project.
   - `pac plugin init` scaffolds `net462`: switch `<TargetFramework>` to `net48` right after init.
2. **Always scaffold with `pac plugin init`.** It generates `PluginBase.cs` and the correct `.csproj` NuGet package configuration.
   - For a **plug-in package**, the default for new projects, pass `--skip-signing`. Packages don't need signed assemblies, and if one assembly is signed, every assembly it depends on must be signed too.
   - Keep the generated strong-name key (`.snk`) only for a project registered as a plug-in **assembly**: signing is mandatory there.
3. **Ask the user for the root namespace before scaffolding — never invent it.** Recommend `Company.Team.Project`:
   - `Company`: the organisation.
   - `Team`: often the solution publisher, but not always.
   - `Project`: the project code.

   Keep it consistent with the solution publisher and the project code, both recorded in `README.md`. For example, publisher *Contoso Sales* with project code `crm` gives `Contoso.Sales.Crm`. Early-bound classes go in `<RootNamespace>.Models`.
4. **Set the NuGet package id once.** On the server, the package is named `{publisher prefix}_{package id}`, and that name is permanent once registered.
5. **Bump the build or revision part of `AssemblyVersion` and `FileVersion` before every release.**
   - Never change the major or minor part of a registered assembly: on solution import it becomes a different assembly, and existing steps keep pointing to the old one.
6. **Never hand-edit the generated early-bound classes** in `Models/`. They are build output; regenerate them with `pac modelbuilder build` when the schema changes (see `ppbp-dv-plugins-overview`).

## PAC CLI workflow

### 1 — Scaffold the project

```sh
pac plugin init --outputDirectory <ProjectName> --author "<Author>" --skip-signing
```

This generates `PluginBase.cs`, `<ProjectName>.csproj` and a sample plugin file (plus `<ProjectName>.snk` without `--skip-signing`). After init:

- Set `<TargetFramework>` to `net48`.
- Set `<RootNamespace>` to the namespace the user confirmed (best practice 3).
- Update the NuGet metadata (`PackageId`, Company, Description).

### 2 — Generate early-bound classes

```sh
pac modelbuilder build \
  --outdirectory <ProjectName>/Models \
  --namespace <RootNamespace>.Models \
  --environment https://<org>.crm.dynamics.com/ \
  --emitfieldsclasses \
  --generateGlobalOptionSets \
  --entitynamesfilter "table1;table2;table3"
```

Do **not** add `--generatesdkmessages`: it floods the project with SDK message classes that are not needed.

The generated `Models/` are **build output — never hand-edit them**. When the schema changes, re-run this command to regenerate. Manual edits are lost on the next run and diverge from the live schema.

### 3 — Increment the version before every release build

In `.csproj`, bump the build or revision part of both fields:

```xml
<AssemblyVersion>1.0.1.0</AssemblyVersion>
<FileVersion>1.0.1.0</FileVersion>
```

Use **Major.Minor.Build.Revision**:

- Build or Revision for every release.
- Major and Minor only for a deliberate new assembly, together with a step migration.

### 4 — Release build

```sh
dotnet clean && dotnet build -c Release
```

`dotnet clean` is mandatory: without it the NuGet package is not regenerated, and the version bump is silently ignored.

The build produces `bin/Release/net48/<ProjectName>.dll` and `bin/Release/<PackageId>.<Version>.nupkg`. **The `.nupkg` is the deployable artifact**; the `.dll` is just an intermediate one.

### 5 — Register and deploy

The official `dataverse:dv-overview` skill owns the registration procedure: the first registration of the `.nupkg` goes through the Web API, later builds through `pac plugin push`. Whatever tool runs it, deploy only to the dev environment (`.env.dev`), into its unmanaged solution, and record the package id with the project.

For **cross-environment promotion**, the package ships inside a solution exported and imported with the official `dataverse:dv-solution` skill. That is the ALM path, not a per-iteration push.

## Common issue: dotnet clean and version bumps

Skipping `dotnet clean` before a release build silently deploys the old content even when `.csproj` has a new version number, because the NuGet package is not regenerated. Always run `dotnet clean && dotnet build -c Release`.

## Anti-patterns (DO NOT DO)

| Anti-pattern | Correct approach |
|---|---|
| Skipping `dotnet clean` before a release build — the NuGet package is not regenerated. | Always run `dotnet clean && dotnet build -c Release`. |
| Creating plugin projects by hand without `pac plugin init` — misses PluginBase and the correct NuGet config. | Always scaffold with `pac plugin init`. |
| Inventing the root namespace, or using the project folder name as is. | Ask the user; recommend `Company.Team.Project`, consistent with the publisher and the project code. |
| Keeping the scaffolded `net462`, or targeting `net8.0` for a plug-in — `net8.0` is for client-side SDK code only. | Target `net48` for every plug-in project. |
| Signing the assemblies of a plug-in package without a reason — every dependency must then be signed. | Scaffold packages with `--skip-signing`; sign only assembly-registered projects. |
| Changing the major or minor version of a registered assembly — it becomes a different assembly on import, and steps keep the old one. | Bump build or revision only. |
| Pushing a build to UAT or prod, or to whatever environment the pac profile points to. | Deploy to dev only, with the environment passed explicitly; promote through the managed solution. |
| Hand-editing a generated early-bound class in `Models/` — lost on the next regeneration and diverges from the live schema. | Never edit generated classes; re-run `pac modelbuilder build` to regenerate. |

## Skill boundaries

This skill covers plug-in project scaffolding, versioning and build. It does not cover:

- Domain orientation and repository layout → `ppbp-dv-plugins-overview`
- Registration, first upload, `pac plugin push` (procedure) → `dataverse:dv-overview`
- Step plugin implementation, execution pipeline, images → `ppbp-dv-step-plugin`
- Custom API design and implementation → `ppbp-dv-custom-api`
- Solution packaging, export/import (the authority for shipping the package) → `dataverse:dv-solution`, `ppbp-alm-solutions`
