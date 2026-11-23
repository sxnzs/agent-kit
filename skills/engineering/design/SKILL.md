---
name: design
description: Architect deep modules, maintain domain models (CONTEXT.md and docs/adr/), and build throwaway prototypes. Use when shaping interfaces, refactoring shallow modules, or resolving ADRs. Not for bug diagnosis (use debug) or UI/visual/motion craft (use ui-design).
---

# Design

Build **deep modules** behind clean **seams**, keep the codebase garden weeded, and anchor vocabulary in `CONTEXT.md` and `docs/adr/`.

## Domain Context First

Before exploring or proposing changes, check if `CONTEXT.md` (or `CONTEXT-MAP.md`) and `docs/adr/` exist. Read ADRs touching the target area and use the glossary's exact terms. Proceed silently if they do not exist yet; create them lazily using [formats.md](references/formats.md). Surface any ADR conflict explicitly (`Contradicts ADR-NNNN, worth reopening because...`).

## Deep Modules & Garden Guardrails

Use these terms precisely: **Module** (unit with interface + implementation), **Interface** (signature, invariants, ordering, and errors a caller or test must know), and **Depth** (capability per unit of interface). Also keep **Seam** (location of the interface), **Adapter** (concrete implementation at a seam), **Leverage**, and **Locality** distinct.

- **Apply the deletion test**: if deleting a wrapper or helper concentrates complexity cleanly rather than scattering it, inline or delete it.
- **Ban nuance-heavy interfaces**: shrink parameter counts, avoid boolean mode flags, and hide state/coordination behind one cohesive seam.
- **Encode boundaries in layout**: place code where ownership and dependencies are obvious from directory and module structure; keep an adapter behind a seam only when implementations actually vary.
- **Eliminate escape-hatch comments**: replace `TODO`/`FIXME`/apology comments explaining fragile workarounds by fixing the seam or deleting the dead path.
- **Design for testability**: accept dependencies instead of constructing them inline; return values instead of mutating caller state; test at the public interface (`the interface is the test surface`).
- **Run the repo's static checks/linters** after structural edits so boundary, type, and lint rules verify the new shape.

When refactoring an area: scope to hot spots (`git log --oneline`) or the requested subsystem, evaluate 2+ radically different interface shapes, and pick the deepest one.

## Throwaway Prototypes

Use a prototype only to answer a sharp design question before committing to production code:

- **Logic / state model**: write a single self-contained HTML file (or minimal script) with free-play controls and guided edge-case walkthroughs that print full state after every action.
- **UI exploration**: render distinct variations on one route switched via query param or a minimal switcher bar.

Rules: mark prototypes clearly as throwaway, keep state in memory (no persistence/polish/tests), record the settled verdict in the spec/issue or ADR, and delete throwaway files before landing on the default branch.
