---
name: ship
description: Commit and push finished work cleanly across every touched repository.
disable-model-invocation: true
---

# Ship

The user asked to commit, so commit and push every repo the work touched. Their rule: commit means
push to every remote unless they said local only.

## Steps

1. List the repos this session changed. For a wide sweep, use the host's repo status skill when
   one is installed instead of rescanning. Read `git status --short` and `git diff --stat` in
   each one.
2. Stage only the files this work changed. Leave out scratch output, `__pycache__`, build dirs,
   and changes someone else made (an unfamiliar diff hunk counts). Name what you left out.
3. Write the message: a subject that says what changed, then why. For a fix, name the confirmed
   cause; for a change with a behavior contract, the check that proves it. End it with the
   attribution lines the session gives you.
4. Push to every remote in `git remote`. A repo with no remote is reported as `no remote`, not
   skipped silently.
5. A folder that is deliberately not git gets its own save step instead, such as the project's
   backup command. Report it.
6. If a hook or the guard refuses a commit or push, stop for that repo. Do not reword or reroute to
   get past it. Collect it for the closing script.

## Report

One table: repo, commit (short sha and subject), pushed to, left out. Then the blocked actions as
one numbered script in a code block, if any.
