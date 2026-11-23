---
name: bonsai
description: Refactor a whole repo in five gated phases so boundaries, bans, and checks live in tools instead of prose.
disable-model-invocation: true
---

# Bonsai

Turn the target repo into a high-trust, deterministic environment: architectural invariants, security boundaries and code quality are enforced by the compiler, linter and an automated verification harness, not by prose instructions.

This is a whole-repo, multi-session rewrite. Run it only on an explicit request that names or implies one repo. For lighter onboarding or fixing what makes agent sessions stumble without a full rewrite, tell the user to run the agent-setup skill.

## Preflight

1. Resolve the target repo root (`git rev-parse --show-toplevel` from the path the user named, else the cwd). Stop and ask if it resolves to `$HOME`, a holding or archive folder, or a checkout the user does not own.
2. Read the repo's own `AGENTS.md`, build files and CI to find the real build, lint, typecheck and test commands. The repo's commands win over anything named here.
3. Require a clean tree, then record the baseline: exit status of build, lint, typecheck and tests. If the baseline is red, report it and stop; a harness built on a broken base proves nothing.
4. Work on a branch. Keep a one-line `LATEST` in the repo's plans or artifacts folder naming the current phase and next step, and read it first on resume.
5. Names such as `core/`, `product/`, `scripts/verify` and the example APIs below are illustrations. Map them onto the repo's language and existing layout before restructuring anything.

## Routing

- **Planning (strongest reasoning available):** Phase 1 boundary design, Phase 2 abstraction design and security audit, Phase 4 harness and invariant design.
- **Mechanical execution (fast model or executor subagent, when the host has one):** Phase 2 call-site migrations, Phase 3 cleanup, repetitive test and lint fixes. Give it exact paths and the gate command.

## Hard boundaries

- **Zero escape hatches:** no inline lint-disable comments (`// eslint-disable`, `#[allow(...)]`, `# noqa`, `@ts-ignore`) to get past a new rule. Fix the root cause.
- **Zero legacy residue:** when a new core abstraction or lint rule lands, migrate every existing call site in the same phase so no anti-pattern remains for a future agent to copy.
- **No comment slop:** no explanatory or workaround-justifying inline comments. Express intent through types, naming and actionable lint error messages.
- **Gates are hard stops:** a phase is done only when its exit gate command has been run and passed. On a red gate, fix it or stop and report; never start the next phase on a red gate, and never weaken a rule to turn it green.
- **Checkpoint per phase:** after each green gate, update `LATEST`. Commit only if the user asked for commits in this session.

## Phase 1: Enforce architectural boundaries

1. Map all execution and domain boundaries (for example core vs. product, main vs. renderer, UI vs. domain logic).
2. Restructure top-level directories so the boundaries are explicit in the file tree.
3. Configure strict dependency-graph enforcement (Cargo workspace visibility, `dependency-cruiser`, ESLint `no-restricted-imports`, `import-linter`, or the stack's equivalent) to forbid illegal cross-boundary imports.
4. **Exit gate:** build and dependency-graph checks pass with 0 violations.

## Phase 2: Ban nuance-heavy footguns and security sinks

1. Audit the codebase for:
   - Nuance-heavy APIs prone to misuse (for example `useEffect`, raw timers such as `setTimeout` and `requestAnimationFrame`, unchecked casts, ad-hoc state mutation).
   - Root-cause security sinks (unvalidated inputs, unsafe deserialization, injection surfaces).
2. Encapsulate the required low-level operations inside narrow, declarative core abstractions.
3. Add lint rules banning direct use of these APIs and sinks in product code. Every rule must print an actionable error message that points to the approved core abstraction or the root-cause fix.
4. Migrate all existing call sites to the new abstractions.
5. **Exit gate:** linter, type checker and security checks pass with 0 errors and 0 disable pragmas (grep for the pragmas to prove it).

## Phase 3: Prune comment slop and dead code

1. Remove stale, apologetic or redundant inline comments across product code. Keep only public API docstrings and non-obvious invariants that cannot be encoded in types.
2. Add a lint rule forbidding commented-out code.
3. Delete dead exports, unused helpers and deprecated branches.
4. **Exit gate:** zero dead-code warnings; the full test suite stays green.

## Phase 4: Build the verification harness

1. Write a concise feature map of user-facing flows and UI/API entry points to set a shared vocabulary. Reuse the repo's existing map if it has one; otherwise create `docs/agents/feature-map.md`.
2. Build one deterministic CLI entry point (`scripts/verify`, or the repo's existing equivalent) that:
   - runs the application or service,
   - executes end-to-end runtime checks (browser/CDP or CLI harness),
   - emits reviewable artifacts (screenshots, videos or state-transition logs) to `artifacts/verify/`, which must be git-ignored.
3. Add property-based tests (or TLA+/Lean specs for critical state machines and algorithms) so core invariants are checked automatically.
4. Call the Skill tool with "verify-artifacts". Follow it for how to serve, drive, and capture.
5. **Exit gate:** `scripts/verify` exits 0 twice in a row and populates `artifacts/verify/`. Open the artifacts and confirm they show what they claim.

## Phase 5: Minimize prose instructions

1. Audit the repo's own instruction files (`AGENTS.md`, `CLAUDE.md`, rule and skill files inside the repo). Delete every instruction now enforced deterministically by the compiler, type system or linter.
2. Keep only: high-level architectural intent, a pointer to the feature map, and the exact verify command.
3. Never edit instruction files outside the repo (global `~/AGENTS.md`, shared skills, harness config).

## Report

After all phases, or at the phase where you stopped, return a concise report:

1. **Boundary and lint rules added:** each new structural or security rule and its enforcement mechanism.
2. **Abstractions created:** each core wrapper and the count of migrated call sites.
3. **Verification results:** exit status of build, lint, tests and `scripts/verify` against the preflight baseline, plus paths to generated artifacts.
4. **Prose pruned:** the rules removed from the repo's instruction files.
5. **Not done:** phases not reached, gates still red, and anything left uncommitted.
