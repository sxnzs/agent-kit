---
name: handoff
description: Delegate primary-source research, write cross-session handoffs, and script human-only setup wizards.
disable-model-invocation: true
---

# Handoff

Delegate primary-source reading cleanly, pass context between sessions without duplication, and script human-only steps reliably.

## 1. Primary-Source Research

- Dispatch a background subagent with a fresh context window to investigate against **primary sources** (official docs, specs, source code, first-party APIs), never secondary summaries.
- Write findings to a single markdown file matching existing repo conventions (e.g., `research/` or `.scratch/<feature>/`), citing the exact source for every claim.

## 2. Session Handoff

Write a concise handoff document where the project keeps handoffs (`HANDOFF.md`), otherwise its `artifacts/` folder; follow a location the user names, and use `$TMPDIR` only for a throwaway handoff:
- State the goal, current state, next concrete step, and **Suggested skills** (exact skill names from the active repo or global skill library).
- Reference specs, ADRs, tickets, commits, and diffs by path/URL instead of duplicating their text.
- Redact all secrets, tokens, and PII.

## 3. Interactive Bash Wizards (Human-Only Steps)

Use only when steps require a human (credentials, OAuth/dashboard clicks, DNS/registrar cutover, CI secrets); never use for steps an agent can run itself.

1. **Scope stages**: inspect `.env*`, host configs, and CI workflows to list ordered stages, URLs, captured keys, secret vs public input, and targets (`.env`, `gh secret`). Confirm the stage list with the user.
2. **Author from template**: copy [scripts/wizard-template.sh](scripts/wizard-template.sh) to a scratch or `scripts/` path. Keep everything above the `STAGES` marker untouched. Replace the example section using `stage`, `say`, `step`, `open_url`, `ask`/`ask_secret`, `write_env`, `set_secret`/`set_var`, `pause`/`confirm`, and set `TOTAL_STAGES`.
3. **Static check & handoff**: run `bash -n <script>` (and `shellcheck` if installed), `chmod +x <script>`, trace that every captured key reaches its target, and tell the user how to run it. Delete ephemeral wizards once done.
