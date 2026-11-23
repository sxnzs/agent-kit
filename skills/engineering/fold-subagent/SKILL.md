---
name: fold-subagent
description: Fold an unnecessary subagent, router, or specialist into skills and tools in the main loop.
disable-model-invocation: true
---

# Fold a subagent into the main loop

Never fold without an eval. Never fold more than one subagent per change.

## Step 1. Build the eval first

1. Start with 10 golden tasks. Use [eval-template.jsonl](assets/eval-template.jsonl) as the schema.
2. Cover every chain of agents that runs together in production (for example "order lookup then shipping date").
3. Cover every rule the agent must not break.
4. Grade the final message with a rubric first. While an orchestrator exists, also record routing accuracy. After a fold, record whether the right skill loaded or the right tool was called.
5. Work toward task completion grading (did the outcome actually happen).
6. If systems are hard to replay, record timestamps on key events in production so they can be replayed as targeted tests.
7. Run every task at least 2 times, ideally 3. Some breaks appear in only one run out of two.

## Step 2. Baseline

Run the eval on the current system. Save scores per task, not only the total, plus latency and cost per task.

## Step 3. Pick the next candidate

Order by:
1. Most used subagents first.
2. Tightly coupled pairs: they chain on each other's output, touch the same data, or are usually called together. A large share of traffic where A is followed by B means merge A and B.
3. Skip any subagent that meets a keep condition (context bloat, parallel disposable work, tool selection failure). Those stay, called as tools.

Low risk first step if you cannot rewrite yet: expose each subagent to the main agent as a tool with a shared response schema. This gives a baseline without changing the subagent.

## Step 4. Fold one

1. Subagent prompt becomes a skill. Description equals the old routing condition, written as "use when ...".
2. Subagent API calls become tools grouped by intent. Move its preconditions and permission checks into those tools.
3. Its reference material becomes skill reference files or a lookup tool.
4. Remove it from the router or orchestrator.

## Step 5. Compare

1. Run the same eval, same number of runs.
2. Look at which tasks flipped, both directions, not just the total.
3. For every task that broke, read the transcript. Typical cause: the main agent now holds a tool and answers alone, skipping a step the specialist used to enforce. Fix by moving that step into a tool precondition or the skill, not by adding a prompt rule.
4. Iterate on the skill description and tool descriptions until the folded version matches or beats the kept version.

## Step 6. Decide

1. Folded version scores equal or better on quality, and no rule breaks: keep the fold.
2. Worse after reasonable iteration: revert and keep the subagent, called as a tool.
3. Record the decision, the scores and the flipped tasks in `FOLD_LOG.md`.

Then repeat from Step 3.

## Ownership

One small central owner for the system prompt, the shared eval set and approval of new skills and tools. Each team owns its skills and tools and ships them with a few eval cases.
