# Amnesiac Agents Feature Map

Canonical entry points, architectural layers, and runtime verification surfaces for this repository.

## Architectural layers

| Layer | Path | Responsibility | Allowed imports |
| --- | --- | --- | --- |
| Guard core | `guard/` | Policy schema (`policy.json`), Python hook (`guard.py`), JS core (`core.mjs`), parity (`parity.mjs`), policy linter (`lint.py`) | Stdlib / Node builtins only |
| Host adapters | `adapters/<host>/` | Per-host glue for `claude`, `codex`, `opencode`, `pi` | `guard/` and own host directory only |
| Repo tooling | `scripts/` | Verification gate (`verify`), boundary/pragma checker (`check_boundaries.py`), skill validator (`check_skills.py`), listing sync (`sync_listings.py`), JSON merger (`jsonmerge.py`) | Stdlib and sibling `scripts/` modules only |
| Skills | `skills/<bucket>/<name>/` | Self-contained `SKILL.md`, Codex twin (`agents/openai.yaml`), optional `scripts/` and `references/` | Stdlib and same-skill modules only |
| CLI helpers | `bin/` | Standalone session utilities (`cm`, `git-stop-warn.sh`, `milestone-run.sh`) | Standalone |

## User-facing flows and CLI surfaces

1. **Install and uninstall (`./install.sh`)**
   - `./install.sh [--all | --only=claude,codex,opencode,pi,gemini] [--dry-run] [--uninstall]`
   - Symlinks shared instructions (`~/.agents/AGENTS.md`), skills (`~/.agents/skills`), and host adapters; merges JSON config fragments via `scripts/jsonmerge.py`; copies rendered Codex rules.
   - Uninstall removes kit symlinks, unmerges JSON fragments, and restores backups.

2. **Pre-tool guard (`guard/guard.py`, `guard/core.mjs`)**
   - `python3 guard/guard.py --host claude`: reads `{tool_name, tool_input}` JSON on stdin, emits `hookSpecificOutput` with `permissionDecision` (`deny` or `ask`).
   - `python3 guard/guard.py --host codex`: enforces `deny` on stdin JSON; `ask` rules are mirrored in `adapters/codex/rules/agent-kit.rules`.
   - `python3 guard/guard.py --test`: runs the 197 built-in policy cases; `node guard/parity.mjs` asserts 100% Python/JS parity.

3. **Skill catalog and listing sync (`scripts/check_skills.py`, `scripts/sync_listings.py`)**
   - `python3 scripts/check_skills.py [--check-links <dir>]`: validates frontmatter, Codex twins, local links, and skill references across all skills.
   - `python3 scripts/sync_listings.py [--check]`: keeps `README.md`, bucket `README.md`s, `ask-kit`, and `agents/openai.yaml` summaries synchronized with `SKILL.md` frontmatter.

4. **Verification harness (`./scripts/verify`)**
   - Single Layer 2 + Layer 3 gate covering boundaries, zero escape hatches, `ruff` lint, guard parity, skill validation, listing sync, prose lint, shellcheck, motion JS tests, property-based invariants, and live throwaway-HOME install/uninstall + guard CLI probes.
   - Emits inspectable artifacts to `artifacts/verify/` (git-ignored).
