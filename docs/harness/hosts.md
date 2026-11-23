# Per-host notes

`agent-kit` uses one source of truth (`~/agent-kit`) and links each host to the primitives it supports.

## Claude Code

- **Skills:** symlinked into `~/.claude/skills/*` (also available via `/plugin marketplace add sxnzs/agent-kit` + `/plugin install agent-kit@agent-kit`).
- **Instructions:** `adapters/claude/CLAUDE.md` is linked to `~/.claude/CLAUDE.md` and imports `~/.agents/AGENTS.md`. If you already have a `CLAUDE.md`, `install.sh` keeps it and adds the import line at the top.
- **Guard:** `PreToolUse` hook runs `guard/guard.py` (merged into `~/.claude/settings.json`).
- **Subagents:** `verifier.md` symlinked into `~/.claude/agents/`.
- **Code mode:** off by default; `cm claude` turns it on for one session (see `CODEMODE.md`).

## Codex

- **Skills:** read from `~/.agents/skills/*` (invoke user-invoked skills with `$name`).
- **Instructions:** `~/.codex/AGENTS.md` symlinked to `AGENTS.md`.
- **Guard:** `hooks.json` runs `guard/guard.py` for deny rules; `adapters/codex/rules/agent-kit.rules` is **copied** with `@KIT@` set to the kit path (Codex ignores symlinked rules files) for ask rules.
- **First run:** open Codex once after install and approve the hook in `/hooks`.
- **Config:** `~/.codex/config.toml` is created from `adapters/codex/config.toml` only if missing.

## OpenCode

- **Skills:** reads both `~/.agents/skills` and `~/.claude/skills`. If it warns about duplicate skill names, set `OPENCODE_DISABLE_CLAUDE_CODE_SKILLS=1`.
- **Instructions:** loaded via `opencode.json` `instructions`, or `~/.config/opencode/AGENTS.md`.
- **Guard:** plugin symlinked to `~/.config/opencode/plugins/agent-kit-guard` (uses `guard/core.mjs`).
- **Config:** merged into `~/.config/opencode/opencode.json`. If you use `opencode.jsonc`, merge `adapters/opencode/opencode.fragment.json` by hand.

## Pi

- **Skills:** read from `~/.agents/skills/*` (invoke user-invoked skills with `/skill:name`).
- **Instructions:** `~/.pi/agent/AGENTS.md` symlinked to `AGENTS.md`.
- **Guard:** extension symlinked to `~/.pi/agent/extensions/agent-kit-guard.ts` (uses `guard/core.mjs`).
- **Verification:** `/verify` prompt symlinked to `~/.pi/agent/prompts/verify.md` (runs a fresh `pi -p`).

## Gemini / Antigravity

- **Skills:** `~/.gemini/config/skills` symlinked to `~/.agents/skills` (so both `agent-kit` skills and any extra skills in `~/.agents/skills` are visible).

## Cursor

- **Plugin install:** clone the repo into `~/.cursor/plugins/local/agent-kit` and restart Cursor. It reads `.cursor-plugin/plugin.json` and loads `skills/engineering`, `skills/productivity`, and the verifier agent. `install.sh` does not touch Cursor.

## Private overlay

When `~/.config/agent-kit/AGENTS.md` or `~/.config/agent-kit/CLAUDE.md` exists, `install.sh` links hosts to your copy instead of the kit's file. Set `AGENT_KIT_LOCAL` to use another folder.
