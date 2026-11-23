---
name: agent-architecture
description: Design, review, or simplify an AI agent or harness. Use when deciding whether to keep subagents or pipelines, or diagnosing why an agent is slow or bloated.
---

# Agent architecture

Default design: one model, one context window, an open tool loop, and context loaded only when needed. Every extra agent, router, or pipeline stage must earn its place with measured evidence.

## Inverse Trust Pyramid & Garden discipline

Push reliability downward in the trust stack, and tend the codebase as a garden (prune workarounds, dead paths, and escape-hatch comments, because agents imitate what they see in the tree):

1. **Layer 1 (Architecture & layout)**: clean boundaries, typed tool schemas, hard preconditions inside tools.
2. **Layer 2 (Static analysis & hooks)**: linters, typecheckers, harness hooks, `guard/policy.json` deny/ask gates.
3. **Layer 3 (Verification artifacts)**: reproducible tests, screenshots, recordings, state diagrams.
4. **Layer 4 (Prose)**: prompts, `AGENTS.md`, skills. Last resort; promote repeated corrections downward to Layers 1 to 3.

## The loop

1. Each turn the model emits a batch of tool calls; the harness runs them in parallel and returns raw results to the same model, which plans in context on turn one and revises mid-run.
2. The loop stops on an answer, user question, or budget (turns, cost, time). A verifier check may run after the answer.

## The seven primitives

| Primitive | Layer | Holds | Loads |
|---|---|---|---|
| Tool | L1/L2 | Actions, live data, typed outputs, preconditions | On demand via tool search when many |
| Hook / rule | L2 | Non-negotiable gates: deny, ask, validate, audit | Always by harness; invisible until fired |
| Budget | L2 | Turn, cost, and time limits; write gates | Harness |
| Subagent | L1 | Isolated context boundary | Only under the three conditions below |
| Skill | L4/L3 | Procedures, judgment calls, deterministic `scripts/` | Description always (model-invoked) or explicit call only (user-invoked); body on demand |
| Knowledge | L4 | Reference facts: policies, specs, definitions | Via lookup tool or skill reference file |
| System prompt | L4 | Identity, voice, universal invariants | Always. Keep short, one owner |

- **Primitive definitions, tool grouping, and subagent costs**: read [primitives.md](references/primitives.md).
- **Decision tree for where a rule, fact, or step belongs**: read [placement.md](references/placement.md).
- **Per-host file paths (Claude Code, Codex, OpenCode, Pi)**: read [hosts.md](references/hosts.md).

## Keep or add a subagent only when

1. The single loop shows measurable degradation from context bloat, or
2. Several tasks must run in parallel with fresh disposable context, or
3. Tool selection fails or instructions conflict and the prompt cannot be fixed.

Split by context boundary (independent research, clean interfaces, black-box verification), not org chart or problem type. Call as a tool with one shared response schema; return raw findings, not lossy summaries.

## Smells to flag

1. Org-chart agents, intent routers, fixed pipelines, or an orchestrator over specialists.
2. Frankenprompt (many authors, conflicting rules) or prose rules trying to replace Layer 2 hooks/linters.
3. Unpruned workarounds, dead paths, or escape-hatch comments that teach agents bad patterns.
4. Pasting retrieved facts into the prompt, >30 to 50 tools loaded at once, or one tool per API endpoint.
5. Legacy scaffolding for weak models ("think step by step", forced step lists) or subtask-only checks without an end-to-end test.

## How to run a review

1. Inventory every prompt, agent, skill, tool, hook, and check with owner and traffic; map each to a primitive and trust layer.
2. Flag subagents failing the three conditions (tell the user to run the fold-subagent skill); move enforceable rules down from Layer 4 prose to Layers 1 to 3.
3. Report as a table (item, current primitive/layer, target, reason, risk), then the first single change and check to judge it. Measure, change one thing, keep what holds up.
