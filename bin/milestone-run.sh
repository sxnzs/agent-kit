#!/usr/bin/env bash
# milestone-run.sh <plan-file> --check '<cmd>' [--budget usd] [--model name]: one headless Claude stage.
# Claude does only the next unfinished stage and stages its files; this script reruns the check and
# commits. The guard refuses agent commits in headless runs, so starting this script is the user's
# approval for that one commit (the guard asks before an agent may start it). Exits 3 when nothing
# was staged and 4 when the check failed, so a loop around it stops at the first failed stage.
set -euo pipefail

usage="usage: milestone-run.sh <plan-file> --check '<cmd>' [--budget usd] [--model name]"
plan=${1:?$usage}; shift
check='' budget=20 model=opus
while [ $# -gt 0 ]; do
  case $1 in
    --check) check=$2; shift 2 ;;
    --budget) budget=$2; shift 2 ;;
    --model) model=$2; shift 2 ;;
    *) echo "$usage" >&2; exit 64 ;;
  esac
done
[ -n "$check" ] || { echo "$usage" >&2; exit 64; }

plan=$(realpath "$plan")
repo=$(git -C "$(dirname "$plan")" rev-parse --show-toplevel)
cd "$repo"
if [ -n "$(git status --porcelain)" ]; then
  echo "milestone-run: $repo has uncommitted changes. Commit or stash them first, so a stage commit holds only that stage." >&2
  exit 2
fi

logs=${XDG_STATE_HOME:-$HOME/.local/state}/agent-kit/milestones
mkdir -p "$logs"
log=$logs/$(basename "$repo")-$(date +%Y%m%d-%H%M%S).log
msg=$log.msg

prompt="Read $plan and any LATEST or HANDOFF file it names. Complete only the next unfinished stage, then stop.
State the stage's scope and acceptance checks first, then run them. The final check for this run is: $check
Update the plan or LATEST with the new state.
If the checks pass, git add exactly the files this stage changed and write a commit message to $msg: what changed, then why.
Do not commit or push. The script that started you commits after it reruns the check.
If a check fails or you are blocked, stage nothing and report why.
Finish with: stage, check results, next stage, and whether the whole plan is done."

set +e
timeout 14400 claude -p "$prompt" --model "$model" --max-budget-usd "$budget" --permission-mode auto </dev/null 2>&1 | tee "$log"
status=${PIPESTATUS[0]}
set -e

if git diff --cached --quiet; then
  echo "milestone-run: nothing staged (claude exit $status). Log: $log" >&2
  exit 3
fi
if ! bash -c "$check" >>"$log" 2>&1; then
  echo "milestone-run: check failed, nothing committed, the stage is left staged. Log: $log" >&2
  exit 4
fi
[ -s "$msg" ] || echo "Stage from $(basename "$plan")" >"$msg"
git commit -q -F "$msg"
echo "milestone-run: $(git log --oneline -1)  log: $log"
