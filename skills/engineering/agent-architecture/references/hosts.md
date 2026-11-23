# Primitive to file, per host

Verified October 2026. Re-check docs after major releases.

| Primitive | Claude Code | Codex CLI | OpenCode | Pi |
|---|---|---|---|---|
| Global instructions | `~/.claude/CLAUDE.md` (can `@import` other files) | `~/.codex/AGENTS.md` | `~/.config/opencode/AGENTS.md` | `~/.pi/agent/AGENTS.md` |
| Project instructions | `CLAUDE.md`, `.claude/CLAUDE.md` | `AGENTS.md` per directory, root first | `AGENTS.md` (falls back to `CLAUDE.md`) | `AGENTS.md` or `CLAUDE.md`, walked up from cwd |
| Global skills | `~/.claude/skills/<name>/SKILL.md` | `~/.agents/skills/` | `~/.config/opencode/skills/`, `~/.agents/skills/`, `~/.claude/skills/` | `~/.pi/agent/skills/`, `~/.agents/skills/` |
| Project skills | `.claude/skills/` | `.agents/skills/` | `.opencode/skills/`, `.agents/skills/`, `.claude/skills/` | `.pi/skills/`, `.agents/skills/` |
| Subagents | `~/.claude/agents/*.md` | `~/.codex/agents/*.toml`, limits in `[agents]` of `config.toml` | `~/.config/opencode/agents/*.md` with `mode: subagent` | None built in. Run `pi -p` in a fresh process, or an extension |
| Hooks / gates | `hooks` in `~/.claude/settings.json`, exit 2 or JSON `permissionDecision` | `~/.codex/hooks.json` (same JSON protocol), plus `~/.codex/rules/*.rules` with `prefix_rule` | `permission` in `opencode.json`, plugins in `~/.config/opencode/plugins/` (`tool.execute.before`, throw to block) | Extensions in `~/.pi/agent/extensions/*.ts`, `pi.on("tool_call")` returning `{ block, reason }` |
| Tools | MCP via `claude mcp add` or `.mcp.json` | `[mcp_servers.<name>]` in `config.toml` | `mcp` block in `opencode.json` | `pi mcp add`, stored in `~/.pi/agent/mcp.json` (project `.pi/mcp.json`), or `pi.registerTool` in an extension |
| Slash prompts | Skills (user invocable) or `.claude/commands/` | Skills | `~/.config/opencode/commands/` | `~/.pi/agent/prompts/*.md` |
| Permissions / sandbox | `permissions.allow/ask/deny` in settings | `approval_policy`, `sandbox_mode` in `config.toml` | `permission` in `opencode.json` (last match wins) | Extension gates |

## Skill invocation and hiding (verified 2026-11-22)

| Host | Version | Hiding mechanism | Hides from model? | Owner invokes hidden skill | Calling sentence (`Call the Skill tool with "<name>".`) |
|---|---|---|---|---|---|
| Claude Code | 2.1.330 | `disable-model-invocation: true` in `SKILL.md` | Yes (verified) | `/<name>` | Passes (loads model-invoked skill) |
| Codex CLI | 0.169.0 | `policy.allow_implicit_invocation: false` in `agents/openai.yaml` | Yes (verified via `codex debug prompt-input`) | `$<name>` or `/skills` | Live exec unverified (local proxy `127.0.0.1:4211` offline); model sees model-invoked skills with `SKILL.md` paths |
| Pi | 1.6.0 | `disable-model-invocation: true` in `SKILL.md` | Yes (verified) | `/skill:<name>` | Passes (loads model-invoked skill) |
| OpenCode | 2.3.2 | `disable-model-invocation: true` in `SKILL.md` | Yes (verified) | `/<name>` or naming the skill | Passes (`Skill` tool loads model-invoked skill) |

Chosen calling sentence across all skills: `Call the Skill tool with "<name>".`

## Shared conventions that work everywhere
* `AGENTS.md` content (Claude Code reaches it through an `@` import in `CLAUDE.md`, or walk-up from `~/AGENTS.md`).
* `SKILL.md` with portable frontmatter (`name`, `description`, optional `disable-model-invocation`, optional `argument-hint`) paired with `agents/openai.yaml` for Codex. `name` must be lowercase letters, digits and single hyphens, match the folder, max 64 chars. Description max 1024 chars (max 160 chars for user-invoked skills).
* `~/.agents/skills/` is read by Codex, OpenCode and Pi. Claude Code reads it via `~/.claude/skills` symlinked to `~/.agents/skills`.
* Claude Code and Codex hooks share the JSON hook protocol, so one script can serve both.
