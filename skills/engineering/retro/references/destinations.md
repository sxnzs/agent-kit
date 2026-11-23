# Destination Rules

Read when executing a destination in Step 3.

## 1. Deterministic check

Choose the strongest deterministic layer that catches the mistake in the repo where it happened: type constraint, linter rule, validator check, unit or integration test, or hook. When implementing a check, confirm it fails on the bad pattern and passes on the fixed pattern.

Guard policy files (such as `guard/policy.json` or host permission rules) are owner-only. Never edit them directly. Put the exact rule name, target pattern, and rationale in the Step 5 report so the owner can apply it.

## 2. Observed skill fix

Edit a skill only when a real session hit a concrete failure, drift, or missing check. Keep edits minimal and prune stale instructions before adding new lines: remove dead workarounds and cached layout inventories, state positive targets over negative bans, keep one authoritative place per rule, and move rare paths into `references/`.

Run the repo's verification gate after editing. Cite the observed failure in the commit message so future readers can verify why the skill changed.

## 3. Rejected idea

Create one markdown file under `.out-of-scope/<short-slug>.md` in the relevant repo with three parts:

```markdown
# <Idea title>

Decision: <what is rejected or excluded>.

Reason: <why it was rejected, grounded in what happened>.
```

## 4. New mistake class (`.corrections`)

Store `.corrections` at the root of the repo where the mistake happened, one line per class:

```text
<short-slug>: <one-sentence description of the mistake class>
```

Search `.corrections` before appending. If the class is already present, do not add a duplicate line. A deterministic check is now due, so route the item back to destination 1 and remove the `.corrections` line once the check lands.

## 5. Durable fact

Do not write or edit memory files during a retro. Report the durable machine fact or owner preference in the Step 5 table with where it came up so the owner decides whether to persist it.
