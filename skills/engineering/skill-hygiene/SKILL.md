---
name: skill-hygiene
description: Create, audit, deduplicate, or prune skills, tool descriptions, and system prompts. Use when writing or auditing SKILL.md files, trimming prompt bloat, or checking agent-facing prose.
---

# Skill hygiene

Skills are Layer 4 prose in the Inverse Trust Pyramid. Keep them lean, change them only for failures observed in real sessions (`SCOPE.md`), and prune stale workarounds. **Whenever an agent gets corrected twice for the same mistake, promote the fix downward into a lint rule, test, or hook instead of adding prose.** For writing style when editing skills, `AGENTS.md`, or prompts, read [agent-facing prose](references/agent-facing.md).

## Writing a new skill

1. **Choose the invocation kind first**: make a skill model-invoked only when the agent or another skill must reach it on its own. Make everything else user-invoked.
2. **Place it**: put daily code workflows in `skills/engineering/`, daily non-code workflows in `skills/productivity/`, and beta skills in `skills/in-progress/`. The folder name is the skill name: lowercase letters, digits, single hyphens, at most 64 chars.
3. **Write the description once**: the frontmatter `description` is the only copy written by hand. For a user-invoked skill, set `disable-model-invocation: true` and write one human-facing sentence for a command list, at most 160 chars. For a model-invoked skill, state what the skill does, then `"Use when"` with one trigger per distinct case, at most 1024 chars.
4. **Codex twin**: create `agents/openai.yaml` with `interface.display_name` and a placeholder `interface.short_description`. A user-invoked skill adds `policy.allow_implicit_invocation: false`.
5. **Calling another skill**: for a model-invoked skill, write `Call the Skill tool with "<name>".` (one skill per call). For a user-invoked skill, write `tell the user to run the <name> skill`. Keep every link and path inside the skill folder.
6. **Body and references**: `SKILL.md` holds steps and routing in under 500 lines. Move path-specific detail into `references/` and state when to read each file. End every step on a condition the agent can check. Any step that dispatches a subagent must start it with a fresh context window. Put deterministic work in `scripts/` and state when to run it.
7. **List and check**: add one line for the skill to its bucket `README.md`, the top `README.md`, and `ask-kit`, under the heading or table for its invocation kind. Run `python3 scripts/sync_listings.py` to copy the summary into those lines and the twin, then run `./scripts/verify` until all stages pass. The validator states each format rule (name, allowed keys, quoting, length limits, twin policy, listings, prose dashes) in its error message, so fix what it reports.

## Auditing a library

For every skill record: name, bucket, invocation kind, description length, body lines, and observed evidence of use. For invocation counts from Claude Code sessions, run `python3 scripts/skill_usage.py` from this skill's folder (`--days N` limits the window). It counts Skill tool calls and typed slash commands and prints `never` for an installed skill with none. Report the counts with their date span. A skill renamed inside the window undercounts, so treat `never` as a question to check, not a reason to delete.

Run `./scripts/verify` first. It reports format, twin, cross-skill reference, and listing errors, so audit by hand only what it cannot see.

Flag and fix:
1. Repeated-correction prose: if a skill or `AGENTS.md` rule exists because an agent erred twice, replace it with a linter, type check, test, or hook (`guard/policy.json`).
2. Hard rules (`"never"`, `"must"`) that the model could skip: move to a hook, rule, or tool check.
3. Wrong invocation kind: a skill that only the owner triggers should be user-invoked with `disable-model-invocation: true` and `policy.allow_implicit_invocation: false`.
4. Vague or overlapping model-invoked descriptions: sharpen triggers or split/exclude neighbors.
5. Unused skills, dead workarounds, speculative guardrails, or volatile facts inside a body: delete, record rejected ideas in `.out-of-scope/`, or move facts to `references/` or a lookup tool.
6. Old-model scaffolding (forced numbered thinking, `"think step by step"`, repeated reminders, ALL CAPS warnings, over-constraining examples): remove and verify.

## Auditing tool descriptions and system prompts

1. Over 30 to 50 tools loaded at once: group by intent or defer loading; merge near-duplicate tools.
2. Ambiguous tool descriptions: state clearly when to use each tool versus its neighbors.
3. System prompt lines that are procedures, facts, or hard enforcement: move to skill, knowledge, or hook.
4. Conflicting rules from multiple authors: pick one voice, one owner.

## Output

A table of findings (item, issue, fix, risk), then the edits as a diff. Change one thing, run `./scripts/verify`, and keep what holds up.
