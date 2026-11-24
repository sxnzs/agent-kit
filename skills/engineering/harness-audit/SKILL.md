---
name: harness-audit
description: Audit local agent CLI and desktop setups using raw session telemetry, hook benchmarks, and a fresh red team check.
disable-model-invocation: true
---

# Harness audit

Audit a local coding agent setup (Claude Code CLI, Claude Desktop, Codex, OpenCode, or Pi) from raw evidence rather than surface config reads. Read [host paths and probes](references/hosts.md) for per host config, hook, transcript, and smoke test locations.

Never read or print credential stores (`auth.json`, `.credentials.json`, `.env`, shell secrets files, keychains). Move stale files to a dated holding folder instead of deleting them.

## 1. Inventory configs and contradictions

Read the active host config files listed in [host paths and probes](references/hosts.md) (for `~/.claude.json`, inspect top level keys only).

Check for:
- Cross file permission contradictions (`allow` overriding `ask` or `deny`).
- Secret paths written in prompt prose instead of deterministic deny rules.
- Conflicting or mismatched model and effort settings across CLI and desktop.
- Hardcoded home directory assumptions in global settings (`~` as a trusted repo).
- Dead project paths, stale `.bak` files, disabled plugin auth caches, and redundant skill overrides.

Done when every contradiction and stale entry is listed with file path and line number.

## 2. Benchmark hooks and measure baseline context

Run a warm median of at least 10 wall clock timings (discarding the first cold run) on every configured hook using realistic harmless JSON payloads. Flag any hook spawning redundant subprocesses or any `PreToolUse` chain exceeding the target budget (for example over 30ms median for a single Python guard hook, or over 50ms for a multi hook chain).

Measure the byte and approximate token (`bytes / 4`) footprint of always loaded instructions, memory files (`MEMORY.md` on Claude: flag over 4KB or 40 lines), active skills, and global MCP servers.

Done when warm hook latencies and baseline context counts are recorded.

## 3. Mine raw session telemetry

Scan the last 30 days of main session transcripts for the target host (skip subagent files; see [host paths and probes](references/hosts.md)). Run a short local Python script to aggregate counts instead of loading raw JSONL into context:
- Count sessions started outside a git repo (for example `~` or a parent workspace directory).
- Rank tools by call volume and error rate; flag high error MCP servers or repeated hook blocks.
- Extract user correction and frustration turns and cluster them by root cause (incomplete steps, config drift, hook misfires, tool errors).

Done when the top failure clusters are backed by session and turn counts.

## 4. Run a fresh red team check

Dispatch a read only subagent with a fresh context window and the target config file paths only (do not pass your conclusions). Include these explicit read boundaries in the subagent brief: never read or print credential stores, and inspect `~/.claude.json` top level keys only. Ask it to find contradictions, security gaps, and performance bottlenecks. On hosts without built in subagents (for example Pi), run an isolated `pi -p` pass or note the limitation and perform an explicit checklist recheck. Merge any findings you missed.

Done when the independent review is merged into the diagnosis.

## 5. Present decisions and apply approved fixes

Lead with the diagnosis, top 3 decisions with concrete options, and a phased cleanup plan. If the user asked for a read only audit or declines edits, stop here.

After the user approves edits:
1. Copy backups of all target configs into `~/.local/holding/<topic>-YYYYMMDD/` before editing.
2. Apply approved fixes and move superseded hooks, stale backups, and unused files into the holding folder.
3. Run or install a deterministic doctor script checking config validity, 0 cross file contradictions, memory file size limits (where applicable), secret deny coverage, and warm hook latency within budget.
4. Verify the guard safely using the two step sequence in [host paths and probes](references/hosts.md): stdin probes against the guard hook first, then a live CLI smoke test inside a throwaway git repo with a harmless if unblocked probe.

Done when either the user stops at the read only diagnosis, or the doctor check, stdin probes, and live smoke test all pass with 0 errors.

## Handoffs

- Bloated skills, tool descriptions, or instruction prose -> Call the Skill tool with "skill-hygiene".
- Subagent, router, or hook architecture redesign -> Call the Skill tool with "agent-architecture".
- Repository level onboarding or repo specific failures -> tell the user to run the agent-setup skill
