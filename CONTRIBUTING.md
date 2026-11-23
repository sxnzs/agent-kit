# Contributing

Thanks for looking. This kit is one person's daily setup, published so others can copy what works. Changes are welcome when they fit [`SCOPE.md`](./SCOPE.md).

## What gets merged

- A fix for a failure you hit in a real session. Say what happened and on which host.
- A new guard rule with test cases in `CASES` in `guard/guard.py`, mirrored in `adapters/codex/rules/agent-kit.rules` when it is an ask rule.
- Host wiring fixes in `install.sh` or `adapters/`, tested with a throwaway `HOME`.

Speculative guardrails, synthetic evals, and skills that bundle unrelated jobs are declined. `.out-of-scope/` records earlier decisions and the reasons.

## Before you open a pull request

```bash
./scripts/verify
HOME="$(mktemp -d)" ./install.sh --all
```

Both must pass. Keep the pull request to one change, and keep personal paths, machine names, and project names out of skills and `AGENTS.md`. Those belong in your private overlay at `~/.config/agent-kit/`.

## Security

The guard is a seatbelt for honest agent mistakes, not a security boundary. If you find a way an agent can slip a blocked command past it, open an issue with the command and the rule it should have matched.
