---
name: prewalk
description: Land the first real slice or opening section and hand off the live trajectory and check gate to a fast worker.
disable-model-invocation: true
---

# Prewalk

Prime a fast model with one landed example and one deterministic check instead of a wall of instructions. Reading is the bill: hand off a trajectory (landed exemplar, remaining items, exact gate), never a plan document that forces the worker to re-read the repo.

## 1. Pick the mode

- **Code prewalk**: repetitive modules, endpoints, components, migrations, or tests that share one architectural pattern.
- **Prose or Spanish prewalk**: multi-section docs, explainers, scripts, or user-facing technical writing where voice and register must stay natural.
- **Skip prewalk** when the whole job fits in one small edit or when every remaining step is a new architectural decision.

## 2. Lead step (frontier model)

### For code

1. Read the relevant files once and settle types, module boundaries, error handling, and test style.
2. Land the **first complete vertical slice** (implementation + test) cleanly, with no comment slop or lint bypasses.
3. Run the repo's real verification command (`./scripts/verify`, `cargo test`, `tsc`, `eslint`, or equivalent) until it passes with 0 errors.
4. Hand off a compact trajectory packet:
   - **Exemplar**: exact path(s) of the landed slice to mirror.
   - **Remaining items**: ordered checklist of the parallel units to build.
   - **Gate**: exact shell command that must exit 0 after each unit.
   - **Stop conditions**: anything that requires handing back instead of guessing.

### For prose or Spanish

1. Call the Skill tool with "writing". Pass its AI-tells and neutral Latin American Spanish reference files to the walker as needed for the target language.
2. Write and lock the **first section or opening beat** so the exact cadence, clause length, vocabulary, and term names are visible on disk.
3. Run the deterministic prose check on the exemplar so the baseline is clean:
   - Repo linter when present, or
   - The prose check command that `writing` names.
4. Hand off the exemplar path, fixed glossary of technical terms, remaining section outline, and exact lint command.

## 3. Walker step (fast model, e.g. DeepSeek V4.1 Flash 1017)

1. Read the landed exemplar first. Match its exact structure, imports, error handling, naming, and tone. Do not invent parallel helpers, swap synonyms for defined terms, or shift register.
2. Never add comments to explain obvious code or excuse shortcuts. Fix the root cause.
3. Work one item at a time. After each item, run the gate command and fix every reported error or warning before moving on. Inspection alone is not proof.
4. For Spanish or human-facing prose, run `check_prose.py` (or the repo linter) on every drafted section and eliminate dashes, calques, filler openings, and contrast templates before returning.
5. **Stop and hand back** instead of improvising when you hit:
   - a new structural seam not covered by the exemplar,
   - an ambiguous requirement or missing source fact, or
   - two consecutive failures on the same error.

## 4. Critic seam (required for long prose and Spanish)

The producer never grades its own prose.

- **Code**: if the gate covers types, lint, boundaries, and tests, only run a frontier diff review when the diff crosses a tricky boundary or changes public behavior.
- **Spanish and human prose over ~500 words**: flash models drift back toward stiff syntax and English calques across long runs. Once the walker finishes drafting and passes the deterministic lint check, run one short frontier pass for voice, cadence, and factual alignment against sources.

## Re-arming

One prewalk per structural pattern. Re-arm the lead step only when the pattern changes.

For before and after quality prompts when tuning a fast worker, read [references/benchmark.md](references/benchmark.md).
