---
name: retro
description: Run a session retrospective and promote repeated corrections downward into deterministic checks.
disable-model-invocation: true
---

# Session Retrospective

Turn session corrections into lasting changes. Promote every repeated correction downward into a deterministic check (lint rule, type check, test, hook, or cleaner module boundary) before adding prose to `AGENTS.md` or skills. Keep steering text crisp: delete no-ops and stale caches, prefer positive targets over negative bans, keep one source of truth per rule, and disclose rare branches behind pointers.

## 1. Collect

List every correction the owner gave in this conversation, every repeated manual step, and every place a skill or rule misled the agent.
Done when each item is one line with a quote or a file reference.

## 2. Check the past, on request

Only when the owner asks to look across earlier sessions, use the recall skill to search them for the same class of correction. Read [past-session search](references/past-sessions.md) when this path applies.
Done when either no past search was requested, or every matching earlier hit is added to the list with its session reference.

## 3. Route

Send each item to the first destination that fits. Read [destination rules](references/destinations.md) for file formats, guard boundaries, and steering edits when executing a destination.

1. **Deterministic check**: a check can catch it. Propose the lint rule, test, type, validator rule, or hook in the repo where the mistake happened. Guard policy files are owner-only, so write the proposed change in the report and do not edit them.
2. **Observed skill fix**: a skill behaved wrongly in an observed way. Change that skill, and cite the observed failure in the commit message.
3. **Rejected idea**: the idea was considered and rejected. Add one file under `.out-of-scope/` with the reason.
4. **New mistake class**: the class of mistake is new and no check fits yet. Add one line naming the class to the repo's `.corrections` file. If the class is already listed, a check is now due, so go back to destination 1.
5. **Durable fact**: a fact about the machine or the owner's preferences. State it in the report and do not write memory files.

Done when every collected item has exactly one destination.

## 4. Skip duplicates

Search existing checks, skills, `.out-of-scope/`, and `.corrections` before adding anything. Skip any item already captured by an existing check, skill, or rejection note. A prior `.corrections` entry promotes to destination 1 instead of being skipped.
Done when no new line repeats an existing one.

## 5. Report

Output a table with columns `Item`, `Destination`, and `Change made or proposed`. Include skipped items with the file that already covers them.
Done when the table has one row per collected item.
