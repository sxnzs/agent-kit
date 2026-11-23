---
name: diff-review
description: Verification-artifact-first code review and concise PR summaries. Use when reviewing diffs or PRs. Not for fixing bugs (use debug) or planning new features (use design).
---

# Code Review & PR Summary

Verify with artifacts first and review diffs along independent axes.

## 1. Verification-Artifact-First Code Review

1. **Inspect evidence before opinions**: require passing output from the repo's static checks/linters and tests. For behavioral or UI changes, Call the Skill tool with "verify-artifacts". Require Layer 3 runtime evidence (screenshots, recordings, CLI traces, or property-test outputs).
2. **Pin the diff**: resolve `git diff <base>...HEAD` and locate any originating spec, ADR, or ticket under `.scratch/`, `plans/`, or `docs/adr/`.
3. **Run two independent review axes** (in parallel subagents with fresh context windows for non-trivial diffs; never merge or rerank axes):
   - **Standards**: check repo `AGENTS.md`, `docs/adr/`, and Fowler smell baseline (Duplicated Code, Feature Envy, Data Clumps, Primitive Obsession, Repeated Switches, Shotgun Surgery, Divergent Change, Speculative Generality, Message Chains, Middle Man). Repo rules override the baseline; skip anything static checks/linters already enforce.
   - **Spec**: report missing requirements, unrequested scope creep, and wrong behavior, quoting the spec line for each.
4. Report `## Standards` and `## Spec` separately with total findings and worst issue per axis.

## 2. Concise PR Summary

Skip preambles; use domain terms from `CONTEXT.md` or the repo's feature map:
- **Summary**: smallest view that clarifies the change (shallow file tree, call tree, diff-sketch, or Mermaid).
- **Evidence**: before/after artifacts (`artifacts/`) or failing->passing check output.
- **Merge Danger**: `Door: one-way | two-way` and `Blast Radius: <scope>`.
