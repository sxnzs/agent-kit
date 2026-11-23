---
name: skill-hygiene
description: Create, audit, deduplicate, or prune skills, tool descriptions, and system prompts. Use when writing or auditing SKILL.md files, trimming prompt bloat, or checking agent-facing prose.
---

# Skill hygiene

Skills are Layer 4 prose in the Inverse Trust Pyramid. Keep them lean, change them only for failures observed in real sessions (`SCOPE.md`), and prune stale workarounds. **Whenever an agent gets corrected twice for the same mistake, promote the fix downward into a lint rule, test, or hook instead of adding prose.** For writing style when editing skills, `AGENTS.md`, or prompts, read [agent-facing prose](references/agent-facing.md).

## Writing a new skill

1. **Choose the invocation kind first**: make a skill model-invoked only when the agent or another skill must reach it on its own. Make everything else user-invoked.
2. **Placement and naming**: put daily code workflows in `skills/engineering/`, daily non-code workflows in `skills/productivity/`, and beta skills in `skills/in-progress/`. Folder name equals `name`: lowercase letters, digits, single hyphens, at most 64 chars, unique across all buckets.
3. **Frontmatter**: allowed keys are `name`, `description`, `disable-model-invocation`, and `argument-hint`. Quote any value containing `: ` or starting with a YAML indicator character. Keep `name` unquoted.
4. **Invocation and description**:
   - **User-invoked**: set `disable-model-invocation: true`. Write one human-facing sentence for a command list, at most 160 chars, with no `"Use when"`.
   - **Model-invoked**: omit `disable-model-invocation`. State what the skill does and `"Use when"` with one trigger per distinct case, at most 1024 chars.
5. **Codex twin**: create `agents/openai.yaml` with `interface.display_name` and `interface.short_description`. User-invoked skills add `policy.allow_implicit_invocation: false`; model-invoked skills omit it. Both files must agree.
6. **Calling another skill**: for a model-invoked skill, write `Call the Skill tool with "<name>".` (one skill per call). For a user-invoked skill, write `tell the user to run the <name> skill`. Never link or write a backticked path that leaves the skill folder.
7. **Body and references**: keep `SKILL.md` under 500 lines holding steps and routing. Move path-specific detail into `references/` and state when to read each file. End every step on a condition the agent can check. Any step that dispatches a subagent must start it with a fresh context window. Put deterministic work in `scripts/` and state when to run it.
8. **Listings and checks**: add the skill to its bucket `README.md` under "User-invoked" or "Model-invoked", add it to the top `README.md`, and add every user-invoked skill to `ask-kit`. Run `./scripts/verify` (including `check_prose.py --strict`, no prose dashes) until all stages pass.

## Auditing a library

For every skill record: name, bucket, invocation kind, description length, body lines, and observed evidence of use.

Flag and fix:
1. Repeated-correction prose: if a skill or `AGENTS.md` rule exists because an agent erred twice, replace it with a linter, type check, test, or hook (`guard/policy.json`).
2. Hard rules (`"never"`, `"must"`) that the model could skip: move to a hook, rule, or tool check.
3. Wrong invocation kind: a skill that only the owner triggers should be user-invoked with `disable-model-invocation: true` and `policy.allow_implicit_invocation: false`.
4. Mismatched Codex twin, unquoted `: ` in frontmatter, cross-skill paths, or missing bucket `README.md` / `ask-kit` listings.
5. Vague or overlapping model-invoked descriptions: sharpen triggers or split/exclude neighbors.
6. Unused skills, dead workarounds, speculative guardrails, or volatile facts inside a body: delete, record rejected ideas in `.out-of-scope/`, or move facts to `references/` or a lookup tool.
7. Old-model scaffolding (forced numbered thinking, `"think step by step"`, repeated reminders, ALL CAPS warnings, over-constraining examples): remove and verify.

## Auditing tool descriptions and system prompts

1. Over 30 to 50 tools loaded at once: group by intent or defer loading; merge near-duplicate tools.
2. Ambiguous tool descriptions: state clearly when to use each tool versus its neighbors.
3. System prompt lines that are procedures, facts, or hard enforcement: move to skill, knowledge, or hook.
4. Conflicting rules from multiple authors: pick one voice, one owner.

## Output

A table of findings (item, issue, fix, risk), then the edits as a diff. Change one thing, run `./scripts/verify`, and keep what holds up.
