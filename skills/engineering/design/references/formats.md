# Domain & Decision Formats

## `CONTEXT.md` (Glossary)

Single-context repos use one root `CONTEXT.md` (created lazily when the first domain term is resolved). Multi-context repos use `CONTEXT-MAP.md` pointing to `src/<context>/CONTEXT.md`.

```md
# {Context Name}

{1-2 sentences describing what this context is and why it exists.}

## Language

**{Canonical Term}**:
{1-2 sentence definition of what it IS, not what it does.}
_Avoid_: {rejected synonyms}
```

Rules:
- Pick one canonical term per concept and list rejected synonyms under `_Avoid_`.
- Include only project-specific domain concepts, not generic programming terms.
- Group under subheadings only when natural clusters emerge.

## ADRs (`docs/adr/NNNN-slug.md`)

Create `docs/adr/` lazily when the first qualifying decision lands. Number sequentially from the highest existing file in `docs/adr/`.

```md
# {Short title of the decision}

{1-3 sentences: context, what was decided, and why.}
```

Optional sections (include only when load-bearing):
- `Status: proposed | accepted | deprecated | superseded by ADR-NNNN`
- `## Considered Options`: rejected alternatives worth remembering.
- `## Consequences`: non-obvious downstream effects.

Offer an ADR only when **all three** hold:
1. **Hard to reverse**: meaningful cost to change later.
2. **Surprising without context**: future readers would wonder why it was built this way.
3. **Real trade-off**: genuine alternatives existed and one was chosen for concrete reasons (architectural shape, lock-in, boundary/scope decision, deliberate deviation, or invisible constraint).
