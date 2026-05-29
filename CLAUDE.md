# CLAUDE.md

## Rules

1. **All content is in English** — code, comments, skill bodies, references, commit messages.

2. **Skill naming** — `ppbp-<concept>`, lowercase, hyphens only. Dataverse-specific skills prefix with `dv-` (e.g. `ppbp-dv-metadata`). The directory name must match the `name` field exactly.

3. **Skill description** — written for coding agents. A few sentences: what the skill covers, and crucially **when to load it**. Must let an agent decide in seconds whether this skill is relevant to the current task.

4. **Large code examples go in `references/`** — skill bodies stay concise (< 500 lines). Reference files must not be too implementation-specific; they should illustrate a pattern, not a single project.

5. **Each skill earns its own file** — before creating a new skill, verify the domain is not already covered by an existing one. A skill must represent a distinct, non-overlapping domain. Augmenting an existing skill is preferred over creating a near-duplicate.
