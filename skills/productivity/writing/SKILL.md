---
name: writing
description: Writing workflow from raw fragments through grounded beats to shaped prose. Use when drafting or polishing essays, docs, READMEs, or agent instructions. Not for PR summaries (use diff-review).
---

# Writing

Take an essay, post, or technical piece from raw fragments to finished prose without blurring explore and exploit.

## 1. Explore: Raw Fragments (No Structure Yet)

- Interview the author relentlessly about what they noticed; widen material without outlining.
- Append fragments silently to one markdown file separated by `\n---\n` (single H1 working title only). Re-read from disk before every write so author edits survive.
- Hunt for a **leading word**: one compact metaphor, concrete detail, or coinage the whole piece can hang on.

## 2. Exploit: Structure Beats or Shape Prose

Once the raw pile is fixed (treat the pile file as read-only):

1. **Establish prerequisites**: agree what concepts the reader already knows walking in; **ground** every new concept before any later beat or paragraph leans on it.
2. **Choose openings**: draft 2 to 3 candidate openings implying distinct angles; let the author pick or hybridize.
3. **Build step-by-step**:
   - *Beat mode*: propose 2 to 3 reachable next beats noting what each grounds; append only the chosen beat.
   - *Shape mode*: grow paragraph-by-paragraph; argue deliberately over form (prose for argument, list for parallel items, table for 3+ repeated shapes, quote only when exact wording matters). Cut any paragraph that does not advance the opening's promise.
4. Re-read the draft file before each append; honor inline author edits.

## 3. Finalize & Publish

- **Match target format**: conform to the destination repo's frontmatter, metadata, slug, and draft/publish conventions (never invent schema fields without checking).
- **Tighten & verify**: verify every claim, code snippet, link, and citation against primary files or tool output; cut throat-clearing and redundant transitions.
- **Run repo checks**: run the repo's markdown, link, spell, or site build checks after every edit, plus `python3 ~/.agents/skills/writing/scripts/check_prose.py <file>` on human-facing prose.

## 4. Edit Existing Prose Plain

When the request is to edit a draft, doc, README, or instruction file rather than grow a new piece:

- Change only the requested text. Keep the author's voice, facts, and qualifications; leave code, data, metadata, and link targets intact. Never invent facts or citations; flag the gap instead.
- Consult the [tells checklist](references/tells.md) when a draft sounds formulaic or the request is to remove AI-writing tells.
- For Spanish prose, read [neutral Latin American Spanish](references/spanish-latam.md) for lexicon, English-calque replacements, and before/after examples.
- For skills, `AGENTS.md`, or any text an agent will consume, Call the Skill tool with "skill-hygiene".
- Run `python3 ~/.agents/skills/writing/scripts/check_prose.py <file>` (`--lang es` for Spanish, `--strict` for zero warnings) and fix reported errors before returning.
- Compare the result against the original for altered claims, lost qualifications, and voice drift before returning it.
