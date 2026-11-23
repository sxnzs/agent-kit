#!/usr/bin/env bash
# One command to verify the guard after a policy, rule or helper change.
#   guard/check.sh          lint, python self test, JS parity, Codex rules
# Exits 1 if any step fails.
set -uo pipefail
HERE="$(cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")" && pwd)"
fail=0
step() { printf '\n== %s\n' "$*"; }

step "policy lint"
python3 "$HERE/lint.py" || fail=1

step "python self test"
python3 "$HERE/guard.py" --test | tail -n 1 || fail=1

step "js parity"
if command -v node >/dev/null 2>&1; then
  node "$HERE/parity.mjs" || fail=1
else
  echo "skipped: node is not installed"
fi

if command -v codex >/dev/null 2>&1; then
  step "codex rules"
  rules="${AGENT_KIT_CODEX_RULES:-$HERE/../adapters/codex/rules/agent-kit.rules}"
  for probe in "git commit -m x" "git push origin main" "gh pr create --fill" "npm publish"; do
    if codex execpolicy check --rules "$rules" -- $probe >/dev/null 2>&1; then
      echo "ok    $probe -> prompt"
    else
      echo "FAIL  $probe -> not matched"; fail=1
    fi
  done
else
  printf '\n== codex rules\nskipped: codex is not installed\n'
fi

if [ "$fail" = 0 ]; then printf '\nall checks passed\n'; else printf '\nchecks failed\n'; fi
exit "$fail"
