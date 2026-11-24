# Host Paths and Probes

Read this file before Step 1 when auditing a local agent setup. Never read or print credential files (`auth.json`, `.credentials.json`, `.env`, shell secrets files, keychains).

## Config, hooks, and transcripts by host

| Surface | Claude Code and Desktop | Codex CLI | OpenCode | Pi |
|---|---|---|---|---|
| Config files | `~/.claude/settings.json`, `~/.claude/settings.local.json`, `~/.claude.json` (top level keys only), Desktop config (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS, `~/.config/Claude/claude_desktop_config.json` on Linux) | `~/.codex/config.toml`, `~/.codex/hooks.json`, `~/.codex/rules/*.rules` | `~/.config/opencode/opencode.json` (or `.jsonc`) | `~/.pi/agent/settings.json`, `~/.pi/agent/mcp.json` |
| Always loaded instructions | `~/.claude/CLAUDE.md` (plus `@` imports), `~/.claude/memory/MEMORY.md` | `~/.codex/AGENTS.md` | `opencode.json` `instructions` or `~/.config/opencode/AGENTS.md` | `~/.pi/agent/AGENTS.md` |
| Hooks and gates | `hooks` in `~/.claude/settings.json` (`PreToolUse`, `PostToolUse`, `Stop`, statusline) | `~/.codex/hooks.json` (same JSON protocol), `~/.codex/rules/*.rules` | `permission` in `opencode.json`, plugins in `~/.config/opencode/plugins/` | Extensions in `~/.pi/agent/extensions/*.ts` |
| Session transcripts | `~/.claude/projects/*/*.jsonl` (skip `subagents/` files) | `~/.codex/sessions/**/*.jsonl` | `~/.local/share/opencode/` session storage | `~/.pi/agent/sessions/**/*.jsonl` |
| Read only subagent | Built in subagent | Built in subagent | Built in subagent (`mode: subagent`) | No built in subagent; run an isolated `pi -p` pass or explicit checklist recheck |
| Live CLI smoke test | `claude -p` | `codex exec` | `opencode run` | `pi -p` |

## Safe guard verification

Test the guard in two steps so a broken hook never runs a destructive command against a real repository:

1. **Deterministic stdin probes (first)**: feed JSON tool payloads directly into the configured hook script and confirm expected decisions and zero output on safe commands:
   ```bash
   printf '%s\n' '{"tool_name":"Bash","tool_input":{"command":"git status"}}' | python3 ~/.agents/agent-kit/guard/guard.py --host claude
   printf '%s\n' '{"tool_name":"Bash","tool_input":{"command":"git reset --hard"}}' | python3 ~/.agents/agent-kit/guard/guard.py --host claude
   ```
   For Codex, pass `--host codex` for deny probes and check `~/.codex/rules/*.rules` for ask rules. For OpenCode and Pi, run the guard JS test suite or extension check.
2. **Live CLI smoke test (second)**: create a throwaway git repo under `$TMPDIR` (`git init` with one empty commit and no remote) and run the host's headless CLI (`claude -p`, `codex exec`, `opencode run`, or `pi -p`) inside it. Verify both a harmless read command (`git status`) and a harmless if unblocked guarded command (for example `git push --force origin main` in a repo with no remote) are handled as expected, then remove the throwaway directory.
