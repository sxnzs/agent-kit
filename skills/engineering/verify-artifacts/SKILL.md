---
name: verify-artifacts
description: Produce Layer 3 runtime, browser, CLI, and visual verification artifacts, or done-check claimed work. Use when proving live behavior after UI, route, API, CLI, or host-config changes, or when asked if claimed work is actually done.
---

# Verify Artifacts

Produce inspectable Layer 3 verification evidence (screenshots, recordings, CLI traces, state diagrams, property-test outputs) from live execution rather than line-by-line diff guessing.

## 1. Maintain & Read the Surface Map

- Check for a user-facing feature map (e.g., `docs/agents/feature-map.md` or `README.md`) listing live routes, CLI commands, flags, selectors, and expected states before writing or running checks.
- When adding or changing user-facing surfaces, update the feature map in the same change so runtime checks stay anchored to real entrypoints.

## 2. Run Live Runtime, Browser & CLI Checks

- **Web & host surfaces**: serve over local loopback HTTP (`127.0.0.1`), never `file://`. Verify desktop and mobile viewports, keyboard navigation/focus traps, modals, empty/error states, zero unexpected console errors or third-party requests, and local host/header/redirect checks if host config changed.
- **CLI & API surfaces**: run real end-to-end invocations against disposable fixtures or local servers, checking exit codes, stdout/stderr, and state transitions.
- **Clean teardown**: keep browser profiles and scratch state in `$TMPDIR` (never in tracked repo directories) and stop any temporary servers you started when done.

## 3. Produce Inspectable Artifacts

Write artifacts to the repo's ignored artifact directory (e.g., `artifacts/`) or `$TMPDIR`:
- **Visual**: before/after screenshots or screen recordings covering desktop, mobile, and changed interactive states.
- **Stateful flows**: Mermaid state/sequence diagrams or trace logs showing transitions exercised and invariants held.
- **Formal / property / fuzz checks**: command, seed, invariant tested, iteration count, and pass/counterexample output.

## 4. Report Evidence Plainly

Cite the exact commands run, artifact paths produced, environments/viewports tested, and any skipped checks (with reason). Never claim runtime behavior passed without inspecting the output or image.

## 5. Done-Check of Claimed Work

When asked whether work is really done, or to check another agent's claims:

- **Derive the completion contract** from the user's request and repo requirements. The producer's summary is a starting point, not the conclusion.
- **Inspect the real artifact**: the files, result, or rendered behavior. A passing suite alone cannot prove a promised artifact exists; an assertion recomputed the same way as the implementation proves nothing.
- **Use the cheapest settling checks first** (the repo's own tests, lint, types before builds or logs), and stop once the claim is settled. Attribute each failure: demonstrated defect, missing evidence, or unrelated baseline.
- **Stay read-only**: do not fix or expand the implementation unless asked. Name the smallest repair or missing check that would resolve a blocker. Never relabel self-review as independent.
- **Verdict**: report **PASS** (contract satisfied), **FAIL** (proven material miss), or **UNVERIFIED** (required evidence unobtainable), with what was checked, observed results, and what was skipped.
