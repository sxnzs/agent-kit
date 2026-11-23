# Where does this go?

Ask in order. Stop at the first yes.

1. Must it never be violated, even if the model disagrees? Hook, rule or a check inside the tool.
2. Does it take an action or read live system state? Tool.
3. Is it a fact or document needed only sometimes? Knowledge (lookup tool or skill reference file).
4. Is it how a kind of task is done (steps, order, judgment)? Skill.
5. Is it true for every task, every time? System prompt, in one line.
6. Is it cheap, mechanical and needed almost every time? Harness code.
7. Does it need isolated context because of size, parallelism or verification? Subagent, called as a tool.

## Common moves

| Found | Move to |
|---|---|
| Specialist subagent prompt | Skill |
| Specialist subagent API calls | Tools grouped by intent |
| Router or intent classifier | Skill descriptions plus the model's own choice |
| Planner stage or rule catalog | Plan written in context by the main model |
| "Always check X before Y" in the prompt | Precondition inside tool Y |
| "Never do Z" in the prompt | Hook or rule that denies Z |
| Policy text pasted by code | Lookup tool or skill reference file |
| One agent per permission level | One loop, tools that check the caller's permissions |
| Team specific sentences in the system prompt | That team's skill |
