# ppbp-dataverse-plugins — Agent Orchestration

## Purpose

This plugin covers Dataverse plug-in best practices: project setup conventions, step plugin implementation patterns, Custom API design, IPlugin interface usage, build workflow, and deployment targets. It adds opinionated guidance on top of the official model-driven app and PAC CLI toolchain — there is no single paired official Microsoft skill for this domain.

## Skill load order

Load `ppbp-dv-plugins-overview` first — it contains the repository layout and global conventions (one C# project per plugin, shared assembly pattern, registration tool usage). Then load the task skill matching the current work: `ppbp-dv-step-plugin` for event-driven plugins, `ppbp-dv-custom-api` for Custom API design, or `ppbp-dv-plugin-build` for build and deployment.

## Routing logic

| User intent | Skill to invoke |
|---|---|
| "Create a Dataverse plugin" / "plugin project setup" | `ppbp-dv-plugins-overview`, then `ppbp-dv-plugin-build` |
| "Implement a step plugin" / "register a plugin step" | `ppbp-dv-step-plugin` |
| "Create a Custom API" / "design a Custom Action" | `ppbp-dv-custom-api` |
| "Build and deploy the plugin" | `ppbp-dv-plugin-build` |

## Constraints

No single official Microsoft skill covers Dataverse plug-in development end-to-end. Skills in this plugin stand independently. For PAC CLI commands used during deployment, always refer to the PAC CLI documentation — ppbp-dv-plugin-build does not restate CLI flags. `ppbp-dv-plugin-build` generates project files and may use `Write` and `Edit` tools.
