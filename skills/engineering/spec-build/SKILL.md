---
name: spec-build
description: Turn settled decisions into local specs, wayfinding maps, and vertical TDD slices.
disable-model-invocation: true
---

# Spec & Build

Turn settled ideas into local markdown specs/tickets under `.scratch/<feature>/` and deliver them in vertical test-first slices gated by the repo's deterministic checks.

## Local Issue Tracker (`.scratch/<feature>/`)

- **Spec**: `.scratch/<feature>/spec.md`: Problem Statement, Solution, User Stories, Implementation Decisions (module/interface shapes without brittle file paths), Testing Decisions (seams + prior art), Out of Scope.
- **Wayfinding map** (for multi-session efforts wrapped in fog): `.scratch/<feature>/map.md` holding `Destination`, `Notes`, `Decisions so far` (one-line gists + links), `Not yet specified` (fog), and `Out of scope`.
- **Tickets**: one file per slice at `.scratch/<feature>/issues/<NN>-<slug>.md`, numbered from `01` with `Status: ready-for-agent | claimed | resolved` and `Blocked by: NN | None`. Never combine tickets into one file.
- **Wayfinding rule**: claim one frontier ticket (open, unblocked, `ready-for-agent`), resolve it (research, prototype, grilling, or unblocking task), append `## Answer`, mark `resolved`, and graduate cleared fog into new tickets.

## Tracer-Bullet Slicing

- Slice **vertically**: each ticket delivers a narrow, end-to-end verifiable behavior across all affected layers, sized for one context window.
- Exception for **wide refactors**: use **expand-contract** (add new form -> migrate callers in green batches -> remove old form).
- Confirm the proposed ticket breakdown, seams, and blocking edges with the user before writing tickets.

## Test-First Implementation (TDD)

1. **Agree seams first**: confirm the public boundary under test before writing assertions (unit/integration tests at module seams; browser or end-to-end checks for UI behavior).
2. **Red -> Green vertical cycles**: write one failing test at the seam, observe it fail, write the minimal code to pass it, then repeat. Do not batch all tests upfront (no horizontal slicing).
3. **Avoid test anti-patterns**: never mock internal collaborators, never assert tautologies recomputed the same way as the implementation, and save refactoring for the review pass.
4. **Gate before finishing**: run the repo's static checks, linters, typecheckers, and test suite. For UI or live-surface changes, Call the Skill tool with "verify-artifacts". Confirm every check passes.
