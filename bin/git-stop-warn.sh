#!/bin/sh
# Stop warning, never blocks and never pushes: one line when the session's cwd sits in a git repo
# that is dirty (tracked changes or untracked files) or has commits no remote has. Silent otherwise.
# Emits {"systemMessage": ...} and exits 0: Stop has no additionalContext, and exit 2 would block the
# stop (looping the agent). Read-only git only; optional locks off so it never races a running git.
command -v jq >/dev/null 2>&1 || exit 0
dir=$(jq -r '.cwd // ""' 2>/dev/null)
[ -n "$dir" ] || dir=$PWD
[ -d "$dir" ] || exit 0
export GIT_OPTIONAL_LOCKS=0
git -C "$dir" rev-parse --is-inside-work-tree >/dev/null 2>&1 || exit 0

dirty=$(git -C "$dir" status --porcelain 2>/dev/null | head -n 200 | wc -l | tr -d ' ')
if git -C "$dir" rev-parse --abbrev-ref '@{u}' >/dev/null 2>&1; then
  ahead=$(git -C "$dir" rev-list --count '@{u}..HEAD' 2>/dev/null)
elif [ -n "$(git -C "$dir" remote 2>/dev/null)" ]; then
  # No upstream: count commits no remote-tracking ref has (capped). A repo with no remote stays silent.
  ahead=$(git -C "$dir" rev-list --count --max-count=100 HEAD --not --remotes 2>/dev/null)
fi

msg=
[ "${dirty:-0}" -gt 0 ] && msg="$dirty uncommitted file(s)"
[ "${ahead:-0}" -gt 0 ] && msg="${msg:+$msg, }$ahead unpushed commit(s)"
[ -n "$msg" ] || exit 0
jq -n --arg m "git: $msg in $(git -C "$dir" rev-parse --show-toplevel 2>/dev/null)" '{systemMessage:$m}'
exit 0
