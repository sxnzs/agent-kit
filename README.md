# Amnesiac Agents

[![verify](https://github.com/sxnzs/amnesiac-agents/actions/workflows/verify.yml/badge.svg)](https://github.com/sxnzs/amnesiac-agents/actions/workflows/verify.yml)

One setup for **Claude Code, Codex, OpenCode, Pi, Gemini/Antigravity, and Cursor**, built on the single-loop pattern:
one model, one context, skills and tools that load on demand, hard limits in the harness, and a subagent only when it earns its place.

You edit one place (`~/agent-kit`). Every host reads it through symlinks.

What you get:

- **One instruction file** ([`AGENTS.md`](./AGENTS.md)) shared by every host.
- **24 skills** that load on demand, split into user-invoked workflows and model-invoked helpers.
- **A guard** ([`guard/policy.json`](./guard/policy.json)) that blocks destructive commands and asks before commits, pushes, publishes, deploys, and sends, with the same rules on every host.
- **A fresh-context verifier** subagent per host, for black box checks of finished work.

Requirements: macOS or Linux, `bash`, `python3`, `git`, and `jq` for the Claude Code stop hook. `node` is optional and only enables the guard parity test.

## Install

### Recommended: clone + `install.sh` (all hosts, guards, and adapters)

```bash
git clone https://github.com/sxnzs/amnesiac-agents.git ~/agent-kit
cd ~/agent-kit
./install.sh --dry-run              # preview what will change
./install.sh                        # install for every host detected on this machine
```

Options:

```bash
./install.sh --all                  # wire up all five installer hosts even if not installed yet
./install.sh --only=claude,gemini   # target specific hosts (claude,codex,opencode,pi,gemini)
./install.sh --uninstall            # remove links and merged config entries
```

Existing files are moved to `*.bak.<timestamp>`. JSON configs are merged and your values win. Codex `config.toml` is created only if missing. A `~/.claude/CLAUDE.md` you wrote yourself is kept and only gains one import line.

Read [`AGENTS.md`](./AGENTS.md) and [`adapters/claude/CLAUDE.md`](./adapters/claude/CLAUDE.md) before you install: they are opinionated. The Claude Code rules tell it to commit and push each working, tested change as it goes.

After install: open Codex once and approve the hook in `/hooks`, then restart any running agent.

To update on any machine:

```bash
cd ~/agent-kit && git pull && ./install.sh
```

### Alternative: native plugin install (skills + agents only)

In Claude Code:

```bash
/plugin marketplace add sxnzs/amnesiac-agents
/plugin install amnesiac-agents@amnesiac-agents
```

In Cursor, clone into the local plugins folder and restart Cursor (it skips symlinks that point outside that folder). This path follows Cursor's plugin docs and the manifest validates, but it has not been tested in Cursor yet:

```bash
git clone https://github.com/sxnzs/amnesiac-agents.git ~/.cursor/plugins/local/amnesiac-agents
```

> Native plugin install gives you the skills and the verifier subagent. Use `./install.sh` when you also want the shared `AGENTS.md`, `guard/policy.json` hooks, `bin/cm` code-mode helper, and Codex/OpenCode/Pi/Gemini wiring. The `writing` and `jev-search` skills call their scripts under `~/.agents/skills/`, so those two need `./install.sh`.

## Get started

Two steps:

1. Run [`/ask-kit`](./skills/productivity/ask-kit/SKILL.md) whenever you are unsure which skill fits. It is the only command you need to remember.
2. Invoke a workflow skill directly when you know the stage (e.g. `/spec-build`, `/prewalk`, `/ship`, `/retro`), or let the model-invoked skills (`debug`, `design`, `diff-review`, `verify-artifacts`, etc.) load on demand.

New here? Read the [getting-started guide](./docs/guide/README.md) or the [per-host notes](./docs/harness/hosts.md).

## Usage

Skills are split into **user-invoked** (trigger explicitly: `/name` in Claude Code or OpenCode, `/skill:name` in Pi, `$name` in Codex) and **model-invoked** (loaded automatically when relevant).

```text
/ask-kit I want to refactor this module and add deterministic checks so the same bugs stop coming back
```

```text
/spec-build turn the decisions in our thread into a local spec and vertical TDD slices
```

```text
/ship
```

<details>
<summary>User-invoked skills (13)</summary>

| Skill | Bucket | Purpose |
|---|---|---|
| [agent-setup](./skills/engineering/agent-setup/SKILL.md) | engineering | Onboard a repository for agents and fix recurring session failures without a full rewrite. |
| [ambition-amplifier](./skills/productivity/ambition-amplifier/SKILL.md) | productivity | Push a task higher on Altitude, Depth, and Range using real tools, raw data, and an outside judge. |
| [ask-kit](./skills/productivity/ask-kit/SKILL.md) | productivity | Map every skill by workflow stage so you only need to remember one name. |
| [bonsai](./skills/engineering/bonsai/SKILL.md) | engineering | Refactor a whole repo in five gated phases so boundaries, bans, and checks live in tools instead of prose. |
| [fold-subagent](./skills/engineering/fold-subagent/SKILL.md) | engineering | Fold an unnecessary subagent, router, or specialist into skills and tools in the main loop. |
| [handoff](./skills/productivity/handoff/SKILL.md) | productivity | Delegate primary-source research, write cross-session handoffs, and script human-only setup wizards. |
| [harness-audit](./skills/engineering/harness-audit/SKILL.md) | engineering | Audit local agent CLI and desktop setups using raw session telemetry, hook benchmarks, and a fresh red team check. |
| [next](./skills/productivity/next/SKILL.md) | productivity | Read the current state of the work and recommend one concrete next step. |
| [prewalk](./skills/productivity/prewalk/SKILL.md) | productivity | Land the first real slice or opening section and hand off the live trajectory and check gate to a fast worker. |
| [retro](./skills/engineering/retro/SKILL.md) | engineering | Run a session retrospective and promote repeated corrections downward into deterministic checks. |
| [ship](./skills/engineering/ship/SKILL.md) | engineering | Commit and push finished work cleanly across every touched repository. |
| [spec-build](./skills/engineering/spec-build/SKILL.md) | engineering | Turn settled decisions into local specs, wayfinding maps, and vertical TDD slices. |
| [teach](./skills/productivity/teach/SKILL.md) | productivity | Teach a concept and build lasting understanding through guided practice. |

</details>

<details>
<summary>Model-invoked skills (11)</summary>

| Skill | Bucket | Purpose |
|---|---|---|
| [agent-architecture](./skills/engineering/agent-architecture/SKILL.md) | engineering | Design, review, or simplify an AI agent or harness. |
| [debug](./skills/engineering/debug/SKILL.md) | engineering | Diagnose hard bugs or performance regressions and resolve git merge or rebase conflicts. |
| [design](./skills/engineering/design/SKILL.md) | engineering | Architect deep modules, maintain domain models (CONTEXT.md and docs/adr/), and build throwaway prototypes. |
| [diff-review](./skills/engineering/diff-review/SKILL.md) | engineering | Verification-artifact-first code review and concise PR summaries. |
| [explain-code](./skills/productivity/explain-code/SKILL.md) | productivity | Give the reader a working mental model of code and the evidence behind why it was built that way. |
| [grill](./skills/productivity/grill/SKILL.md) | productivity | Interview the user relentlessly until every branch of the design tree is settled. |
| [jev-search](./skills/productivity/jev-search/SKILL.md) | productivity | Search the web where result relevance matters, ranked by TypeSafe Jev. |
| [skill-hygiene](./skills/engineering/skill-hygiene/SKILL.md) | engineering | Create, audit, deduplicate, or prune skills, tool descriptions, and system prompts. |
| [ui-design](./skills/engineering/ui-design/SKILL.md) | engineering | Design flows, states, and interactions with prototypes, set concrete visual tokens (type, color, theme), and tune animation and gesture physics by observed behavior. |
| [verify-artifacts](./skills/engineering/verify-artifacts/SKILL.md) | engineering | Produce Layer 3 runtime, browser, CLI, and visual verification artifacts, or done-check claimed work. |
| [writing](./skills/productivity/writing/SKILL.md) | productivity | Writing workflow from raw fragments through grounded beats to shaped prose. |

</details>

Skills live in three buckets: [engineering](./skills/engineering/README.md), [productivity](./skills/productivity/README.md), and `skills/in-progress/` (beta, skipped by `install.sh`).

<details>
<summary>What goes where across hosts</summary>

| Primitive | Source in kit | Claude Code | Codex | OpenCode | Pi | Gemini / Antigravity |
|---|---|---|---|---|---|---|
| Global instructions | `AGENTS.md` | `~/.claude/CLAUDE.md` imports `~/.agents/AGENTS.md` | `~/.codex/AGENTS.md` | `opencode.json` `instructions`, else `~/.config/opencode/AGENTS.md` | `~/.pi/agent/AGENTS.md` | not wired |
| Skills | `skills/<bucket>/*` | `~/.claude/skills/*` | `~/.agents/skills/*` | `~/.agents/skills/*` | `~/.agents/skills/*` | `~/.gemini/config/skills -> ~/.agents/skills` |
| Deny gate | `guard/policy.json` | hook runs `guard.py` | hook runs `guard.py` | plugin uses `core.mjs` | extension uses `core.mjs` | not wired |
| Ask gate | `guard/policy.json` | same hook (`ask`) | `~/.codex/rules/agent-kit.rules` | plugin permission hook (`ask`) + `opencode.json` | extension confirm dialog | not wired |
| Verifier subagent | `adapters/*` | `~/.claude/agents/verifier.md` | `~/.codex/agents/verifier.toml` | `~/.config/opencode/agents/verifier.md` | `/verify` runs a fresh `pi -p` | not wired |
| Code mode | harness native | `CLAUDE_CODE_EXPERIMENTAL_CODE_MODE=1` | `features.code_mode = true` | MCP & plugin tools in `execute` | `codemode.mode = "only"` | not wired |

</details>

## Not shipped here

A few things live outside this repo on purpose:

- **Machine- or project-specific skills**: keep them in your own repo and symlink them into `~/.agents/skills/` next to the kit's.
- **MCP server configs** stay per host because config formats differ; keep each host under ~30 loaded tool definitions.
- **Project-level instructions**: copy `AGENTS.md` into a repo root and put repo-local skills in `.agents/skills/` (with `.claude/skills/` symlinked if needed).

## Guard & tools

The guard is a seatbelt, not a sandbox: it pattern-matches tool calls to catch an agent's honest mistakes, and it will not stop a determined attacker. Keep your host's own sandbox and permission settings on.

Every guard refusal names the rule in [`guard/policy.json`](./guard/policy.json) and states the way forward. Do not work around a rule or edit `guard/` without asking the user. Code mode scripts are scanned as shell text while string values of data keys (`content`, `oldText`, `text`, `body`, `message`, `summary`, `prompt`, `markdown`) are treated as prose.

<details>
<summary>Tools in <code>bin/</code></summary>

- `cm`: per-session code-mode helper (see [`CODEMODE.md`](./CODEMODE.md)).
- `git-stop-warn.sh` (Claude Stop): one line when the repo is dirty or has unpushed commits; never blocks.
- `milestone-run.sh <plan-file> --check '<cmd>'`: one headless Claude stage that runs the check and commits on a clean tree.

</details>

## Make it yours

See [`SCOPE.md`](./SCOPE.md): skills change only for a failure observed in a real session.

**Private overlay.** `AGENTS.md` here holds only rules that fit anyone. Put your own version at `~/.config/agent-kit/AGENTS.md` (start from a copy) and `./install.sh` links every host to it instead, so machine names, paths, and personal rules never enter the repo. `~/.config/agent-kit/CLAUDE.md` does the same for the Claude Code rules. Set `AGENT_KIT_LOCAL` to use another folder.

1. **New skill:** add a folder under `skills/<bucket>/<name>/` with `SKILL.md` and `agents/openai.yaml`, list it in the bucket `README.md`, the top `README.md` and `ask-kit`, run `python3 scripts/sync_listings.py` and `./scripts/verify`, then run `./install.sh`.
2. **New hard rule:** add a regex to `guard/policy.json` (and mirror ask rules in `adapters/codex/rules/agent-kit.rules`), add a test case to `CASES` in `guard/guard.py`, and run `./guard/check.sh`.
3. **New global instruction:** only add to `AGENTS.md` if it is true for every task; otherwise make it a skill.
4. **Verify before pushing:** `./scripts/verify` runs guard checks, skill validation, unit tests, prose linting, and `shellcheck`.

Contributions: see [`CONTRIBUTING.md`](./CONTRIBUTING.md).

## License

[MIT](./LICENSE)
