---
name: next
description: Read the current state of the work and recommend one concrete next step.
disable-model-invocation: true
---

# Next

Read the current conversation, decisions, plans, diff, and check results needed to establish where the work stands. Reuse what is already known; do not restart discovery or interview the user for facts available in the project.

Recommend the smallest useful step that resolves the most consequential gap. A missing acceptance check can matter more than adding features; an approved direction calls for execution rather than another options exercise. If the user explicitly reserved a decision, that decision remains next. If nothing remains, say the work is complete. When two gaps compete, take the one that retires the riskiest unknown.

Give one recommendation, the concrete artifact or gap that makes it next, and the observable result that would complete it. Keep the explanation proportional to the decision. Recommend only; do not execute the step. If the user is asking which skill to pick rather than what step comes next, tell the user to run the ask-kit skill.
