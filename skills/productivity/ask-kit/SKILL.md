---
name: ask-kit
description: Map every skill by workflow stage so you only need to remember one name.
disable-model-invocation: true
---

# Ask Kit

Pick the right skill for the user's request. Name the matching skill with a short reason and let the user invoke it (or note that the model can load it automatically). Never invoke any skill from here.

If the user is asking what concrete step comes next in ongoing work rather than which skill fits, tell the user to run the next skill.

Skills marked **(user-invoked)** must be triggered explicitly (`/name` in Claude Code or OpenCode, `/skill:name` in Pi, `$name` in Codex). Skills marked **(auto)** can also load on demand.

## Plan

- `spec-build` (user-invoked): Turn settled decisions into local specs, wayfinding maps, and vertical TDD slices.
- `next` (user-invoked): Read the current state of the work and recommend one concrete next step.
- `ambition-amplifier` (user-invoked): Push a task higher on Altitude, Depth, and Range using real tools, raw data, and an outside judge.
- `grill` (auto): Interview the user relentlessly until every branch of the design tree is settled.
- `design` (auto): Architect deep modules, maintain domain models (CONTEXT.md and docs/adr/), and build throwaway prototypes.
- `ui-design` (auto): Design flows, states, and interactions with prototypes, set concrete visual tokens (type, color, theme), and tune animation and gesture physics by observed behavior.
- `jev-search` (auto): Search the web where result relevance matters, ranked by TypeSafe Jev.

## Build

- `prewalk` (user-invoked): Land the first real slice or opening section and hand off the live trajectory and check gate to a fast worker.
- `debug` (auto): Diagnose hard bugs or performance regressions and resolve git merge or rebase conflicts.
- `verify-artifacts` (auto): Produce Layer 3 runtime, browser, CLI, and visual verification artifacts, or done-check claimed work.

## Review and ship

- `ship` (user-invoked): Commit and push finished work cleanly across every touched repository.
- `retro` (user-invoked): Run a session retrospective and promote repeated corrections downward into deterministic checks.
- `handoff` (user-invoked): Delegate primary-source research, write cross-session handoffs, and script human-only setup wizards.
- `diff-review` (auto): Verification-artifact-first code review and concise PR summaries.

## Write

- `teach` (user-invoked): Teach a concept and build lasting understanding through guided practice.
- `writing` (auto): Writing workflow from raw fragments through grounded beats to shaped prose.
- `explain-code` (auto): Give the reader a working mental model of code and the evidence behind why it was built that way.

## Harness

- `bonsai` (user-invoked): Refactor a whole repo in five gated phases so boundaries, bans, and checks live in tools instead of prose.
- `agent-setup` (user-invoked): Onboard a repository for agents and fix recurring session failures without a full rewrite.
- `fold-subagent` (user-invoked): Fold an unnecessary subagent, router, or specialist into skills and tools in the main loop.
- `harness-audit` (user-invoked): Audit local agent CLI and desktop setups using raw session telemetry, hook benchmarks, and a fresh red team check.
- `agent-architecture` (auto): Design, review, or simplify an AI agent or harness.
- `skill-hygiene` (auto): Create, audit, deduplicate, or prune skills, tool descriptions, and system prompts.

Done when you have named the single best matching skill (or `next` if they want the next work step) and stopped without running it.
