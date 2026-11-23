---
name: grill
description: Interview the user relentlessly until every branch of the design tree is settled. Use when stress-testing an idea, clarifying unsettled requirements, designing a recurring workflow, or when the user says "grill me" or "loop me".
---

# Grill

Interview the user relentlessly until every branch of the design tree is settled and shared understanding is reached. Do not act on the plan until the user confirms.

## Rules of the Interview

1. **Map a design tree.** Every decision branches into the decisions that hang off it.
2. **Work the frontier in rounds.** Ask only questions whose prerequisites are already settled. Bundle the current frontier into one numbered round, attach your recommended answer (`->`) to each question, and wait for replies before computing the next frontier.
3. **Never ask the user for facts.** Dispatch a read-only subagent with a fresh context window or inspect files/tools yourself for codebase facts, existing conventions, or config. Keep running fact lookups non-blocking: ask independent frontier decisions now and hold downstream questions for the next round.
4. **Format each round cleanly:**

```markdown
**Q1: <Decision title>** <concise question with trade-offs/options>
-> Recommended: <choice and 1-line reason>
```

## Optional Side Effects as Decisions Settle

- **Glossary & ADRs**: If the user wants decisions persisted (or asks to grill with docs), Call the Skill tool with "design". Update `CONTEXT.md` lazily when canonical terms sharpen, or record `docs/adr/NNNN-slug.md` when a hard-to-reverse, non-obvious trade-off settles.
- **Workflow specs**: When grilling a recurring automated workflow, target `workflows/*.md` (one spec per loop). Define only what the loop requires: **Trigger** (event or schedule), **Checkpoint** (human gate pushed as far right as possible), and **Brief** (tight decision-ready summary). A workflow spec is done when an implementer can build it without asking a single question.

## Completion

Stop only when the frontier is empty and nothing remains silently assumed. Summarize the settled decisions and confirm before writing code or specs.
