# Primitives in detail

## System prompt
* Owned by one small central owner. Every addition is reviewed.
* Holds identity, voice and the few rules that apply to every task.
* Does not hold procedures (skill), facts (knowledge) or enforcement (tool or hook).
* Audit it with each new model. Remove rules that compensate for old model weaknesses.

## Skill
* A folder with `SKILL.md` (frontmatter `name`, `description`, then instructions) plus optional `references/`, `scripts/`, `assets/`.
* The description is the trigger. Write it as "what it does" plus "use when ...", with the words a user would actually say.
* Body under about 500 lines. Push detail into reference files the skill points to.
* Each skill has an owner and ships with a few eval cases.
* Portable frontmatter: only `name` and `description` (optionally `license`, `compatibility`, `metadata`). Host specific keys break other hosts.

## Tool
* Group by user intent ("find_customer", "update_ticket"), not one per endpoint.
* Above roughly 30 to 50 definitions, selection degrades. Use deferred loading or tool search.
* Preconditions live in the tool: if Y needs X first, Y checks and returns a plain instruction such as "Run lookup_order first".
* Permissions live in the tool: it checks what the calling user may see or do and returns a readable refusal. One loop then serves every access level.
* Mechanical work (payload building, stream parsing, pagination, resume) happens inside the tool, not in the model.

## Hook / rule
* Harness level gates that the model cannot skip: deny, ask, validate, log.
* Use for destructive commands, publishing, sending, secrets, and anything legally or financially binding.
* Return a reason the model can read so it can recover or ask the user.

## Knowledge
* Reference material needed only sometimes.
* Behind a search or lookup tool, or as reference files in a skill.
* Never fetched by code and pasted into every prompt.

## Budget
* Max turns, max cost, max wall time, and write gates, set in the harness.
* The loop ends with a clear status when a budget is hit.

## Subagent
* Own context, own tools, compact return value.
* Justified by context bloat, parallel disposable work, or tool selection failure only.
* Prefer called as a tool. Share one response schema. Main agent verifies claims.
* Known costs: a lossy summary per call, a nested loop of latency per call, a separate prompt, owner and eval set to maintain.

## Code in the harness
* Allowed for context that is cheap and almost always relevant (entity resolution, current user, repo root).
* Not allowed for deciding the plan. The model decides each step.
