# Code mode: off by default, on per session

Code mode is off in every harness's default config. Turn it on for one session with `cm`, which `install.sh` links to `~/.local/bin/cm`. `cm` also exports `CODEMODE_SESSION=1` to that session.

| Command | Runs | Default it leaves alone |
|---|---|---|
| `cm claude [args]` | `claude --settings overlays/claude-codemode.json` | `~/.claude/settings.json` has no `CLAUDE_CODE_EXPERIMENTAL_CODE_MODE` key |
| `cm codex [args]` | `codex -c features.code_mode=true`, and Claude children get the flag | `features.code_mode = false` |
| `cm pi [args]` | `pi --tools +codemode` | no `+codemode` in `defaultTools`, every MCP server `"exposure": "deferred"` |
| `cm opencode [args]` | `opencode … --standalone` with `OPENCODE_CONFIG` set to a generated overlay | every MCP server `"codemode": false` |

`adapters/codemode.json` records these defaults in a machine-readable form, so a config check of your own can fail when a live config turns one on.

## Why each switch looks like this

- **Claude:** leave the key unset. Any value in `settings.json` env, `"0"` included, wins over `--settings`, and Claude then refuses code mode with a warning. An off value inherited from the shell does the same, so `cm` exports `1`.
- **Claude limits:** code mode is confirmed only in an interactive terminal session started from a normal shell. Claude refuses it in a remote or bridged session, including a shell spawned by another Claude session. A code mode session cannot use Remote Control, and it can be resumed only with code mode on. Under `claude -p` the flag is accepted, but the tool list matches a plain run, so treat print mode as unverified.
- **Codex:** every OpenAI model in the catalog has `tool_mode: code_mode_only`, so Codex keeps its JavaScript `exec` tool whatever the feature says. The flag matters only for other providers.
- **Pi:** Pi turns `codemode` on whenever an MCP server with `codemode` exposure connects, and that exposure is the default. With `deferred`, `tool_search` reaches the servers in plain sessions, and codemode scripts still reach them in `cm pi`.
- **OpenCode:** opencode drops a partial server entry, so `cm` writes an overlay with every live server and `codemode: true` to `~/.cache/agent-kit/opencode-codemode.json`. The shared background service ignores a per-launch `OPENCODE_CONFIG`, hence `--standalone`. The `execute` tool stays in every session, because built-in tools and the account's `opencode_console` server use it. With the defaults off, MCP tools are declared directly instead.
