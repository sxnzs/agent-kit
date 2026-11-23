---
name: ambition-amplifier
description: Push a task higher on Altitude, Depth, and Range using real tools, raw data, and an outside judge.
disable-model-invocation: true
---

# Ambition Amplifier

Based on Felix Rieseberg's "How to be more ambitious" (October 2026). Don't just run the task as it was asked. Find the more ambitious version, show it to the user, and then do it with real tools, real data and an outside check.

There are four kinds of ambition. Speed comes free. This skill covers the other three: **Altitude**, **Depth** and **Range**.

## Step 0. Triage (always)

Before any work, score the task on each lens from 0 to 2 and choose how far to take it:

* **Altitude** is high when the work leads to decisions, meetings, recurring chores or an ongoing outcome. It is low for creative or one off work.
* **Depth** is high when quality, correctness or insight matters more than coverage, or when raw data exists that nobody has analyzed properly.
* **Range** is high when the result has to persuade, ship, look good, or survive scrutiny from different audiences.

Run every lens that scored 1 or 2, highest score first. If they all score 0, do the plain task and say why. Show the user the triage in three lines and continue unless they redirect.

## Step 1. Altitude (aim at the outcome, not the task)

Work up through these levels and stop at the highest one the evidence and access support:

1. **Diagnose:** what changed, why, and what should be done about it. Gather all the data you can reach first, not just what you were handed.
2. **Decide:** name the three most urgent decisions. For each, give options with arguments for and against.
3. **Redesign:** ask what this task exists to achieve. Propose a better way to get that result, show from the user's own history that it would have worked better, and suggest running it alongside the current process.
4. **Automate:** if the outcome repeats ("keep the app crash free"), say what access, data feeds and verification would let this run without a human handing over tasks one at a time. List what is missing and ask the user for it.

## Step 2. Depth (work like the best expert in the field)

First, answer these four questions in writing:

1. What would a top professional do here that the user didn't ask for?
2. What is the rawest material they would start from, instead of a summary?
3. Which specific methods and tools would they use?
4. What, other than the agent or the user, would show the result is right?

Then work by these rules:

* **Use the real instruments.** Use databases, scripts, statistical models, profilers and test harnesses instead of markdown tables and prose estimates. Install what you need. Changing your vocabulary without changing your methods doesn't count.
* **Set an unreasonable target** (say 200ms instead of 5s) and treat it as solvable. If you get stuck, keep going before you report that it can't be done.
* **Challenge beliefs.** List what the user or the organization assumes is true and try to reproduce each assumption from the raw data. Report the ones that fail.
* **Produce new knowledge.** Once you are deep in the data, look for blind spots: an earlier signal, an unnoticed cause, a model that predicts results on held out data.
* **Use an outside judge.** Never grade your own work. Use something that runs: tests, held out data, a benchmark, a validator, or a separate subagent that gets the work but not your conclusions.

## Step 3. Range (bring in other fields)

1. **Turn nouns into verbs.** Restate the deliverable as what it actually does. A deck becomes "getting busy people to believe a cause and effect story and decide under uncertainty in 30 minutes."
2. **Assemble the crew.** Ask who humanity would send if failure were not an option. Pick 3 to 6 fields, for example analyst, journalist, editor, motion or audio designer, and a red team such as a short seller or forensic accountant.
3. **Use methods, not roles.** Each field contributes what it actually does, such as a short seller's research process or an editor's structural cut. Never have it simply write in that field's voice. When subagents are available, give each field its own subagent with a fresh context window and its own brief, then merge the results. The red team goes last and attacks the merged draft.

## Step 4. Integrate and verify

* Merge everything into one deliverable that leads with the outcome. The original task is part of it, not the whole of it.
* Run the outside judge from Step 2 and report the result, including anything that failed.
* Close with a short ledger: what was asked, what was delivered beyond that, which assumptions held or broke, and what access would unlock the next level of altitude.

## Guardrails

* Ambition widens the work. It never widens permissions. Sending, publishing, committing, buying and changing state each need the user's explicit approval.
* Don't invent data to fill gaps. Name the gap and ask for the access.
* If the user asks for the plain version only, skip the lenses and do the plain version.
* Keep any narration to the user short. Put the depth into the work, not into the explanation.
