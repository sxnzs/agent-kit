---
name: debug
description: Diagnose hard bugs or performance regressions and resolve git merge or rebase conflicts. Use when something is broken, throwing, flaky, or slow, or when resolving git conflicts. Not for greenfield architecture or specs (use design).
---

# Debug

Find root causes empirically and resolve git conflicts without guesswork.

## Root-Cause Diagnosis Loop

Redact secrets (`<REDACTED>`) in all shown commands, logs, and artifacts.

1. **Build a tight feedback loop first**: construct a single fast, deterministic, agent-runnable command that goes **red** on the exact symptom (failing unit/integration test, headless browser repro, HTTP request, CLI command, or timing probe). For flakes, amplify reproduction rate (loop/stress) before moving on. Never jump to code hypotheses before a red-capable repro exists.
2. **Reproduce & minimize**: run the loop, verify it matches the reported failure, and strip unrelated inputs/steps until every remaining piece is load-bearing.
3. **Hypothesize (3 to 5 ranked)**: state falsifiable predictions (`If <X> is the cause, changing <Y> will <result>`). For performance regressions, measure with a timing baseline or profiler before changing code.
4. **Instrument one variable at a time**: prefer targeted boundary probes or debugger/REPL inspection over broad logging. Tag temporary logs with a unique prefix (`[DEBUG-xxxx]`) so cleanup is one grep.
5. **Regression test & fix**: lock down the minimized repro as a failing test at a real seam, watch it fail, apply the fix, watch it pass, and re-run the un-minimized loop.
6. **Cleanup**: remove all `[DEBUG-...]` instrumentation and throwaway harnesses, run the repo's static checks/linters and relevant tests (plus runtime/browser checks if UI is affected), and record the winning root cause in the commit/report.

## Git Merge & Rebase Conflicts

1. **Inspect state & intent**: check `git status`, conflict markers, and commit messages/issues for both sides to understand why each change exists.
2. **Resolve every hunk faithfully**: preserve both intents where compatible; when incompatible, keep the side matching the merge/rebase goal and note the trade-off. Never invent new behavior and never run `--abort` without asking.
3. **Verify & finish**: run the repo's static checks/linters and affected test suite (plus runtime/browser checks when UI/config changed), fix any breakage, then stage and commit or run `git rebase --continue`.
