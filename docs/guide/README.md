# Getting started with Agent Kit

This guide walks through installing `agent-kit` on a new machine, running your first task, and keeping multiple machines in sync.

## 1. Install on a new machine

```bash
git clone https://github.com/sxnzs/agent-kit.git ~/agent-kit
cd ~/agent-kit
./install.sh --dry-run
./install.sh
```

What `install.sh` sets up:

- Links `~/agent-kit` to `~/.agents/agent-kit` and every skill under `skills/engineering/` and `skills/productivity/` into `~/.agents/skills/`.
- Links `bin/cm` to `~/.local/bin/cm`.
- Wires up every detected host (Claude Code, Codex, OpenCode, Pi, Gemini/Antigravity) with symlinks and non-destructive JSON merges.
- Runs the guard self-test and skill symlink check at the end.

If you want to wire up hosts you haven't installed yet, pass `--all`. To uninstall cleanly and restore backups, run `./install.sh --uninstall`.

## 2. Pick a skill for your first task

You only need to remember one command: `/ask-kit`. Tell it what you are trying to do and it maps your task to the right skill.

Common workflow stages:

| Stage | User-invoked | Auto-loaded |
|---|---|---|
| Plan & shape | `/spec-build`, `/next`, `/ambition-amplifier` | `grill`, `design`, `ui-design`, `jev-search` |
| Build & verify | `/prewalk` | `debug`, `verify-artifacts` |
| Review & ship | `/ship`, `/retro`, `/handoff` | `diff-review` |
| Write & explain | `/teach` | `writing`, `explain-code` |
| Harness & repo setup | `/bonsai`, `/agent-setup`, `/fold-subagent` | `agent-architecture`, `skill-hygiene` |

## 3. Keep machines in sync

Every host reads `~/agent-kit` through symlinks, so pulling updates takes effect immediately. Re-run `./install.sh` whenever new skills or adapters are added:

```bash
cd ~/agent-kit && git pull && ./install.sh
```

## 4. Validate before committing changes

Before pushing changes to `~/agent-kit`, run the full verification gate:

```bash
cd ~/agent-kit && ./scripts/verify
```

It checks guard policies, skill frontmatter and links, unit tests, prose linting, and shell scripts.
