#!/usr/bin/env python3
"""Lint the guard policy: every rule named, unique, valid, with a way forward, and mirrored for Codex.

Run by guard/check.sh. Prints one line per problem and exits 1 when any is found.
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.realpath(__file__))
POLICY = os.environ.get("AGENT_KIT_POLICY", os.path.join(HERE, "policy.json"))
RULES = os.environ.get("AGENT_KIT_CODEX_RULES", os.path.join(HERE, "..", "adapters", "codex", "rules", "agent-kit.rules"))

SECTIONS = [("bash", "deny"), ("bash", "ask"), ("tools", "deny"), ("tools", "ask"),
            ("paths", "deny_write"), ("paths", "ask_write")]
NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
# A blocked agent needs the next step, not just a refusal.
REMEDY_RE = re.compile(r"(?i)\b(user|instead|download, read|list |target |use |pick |delete one|write the file|generate|narrower|ask)\b")
TAG_RE = re.compile(r"^#\s*policy:\s*(.+)$", re.MULTILINE)
HOOK_ONLY_RE = re.compile(r"^#\s*hook-only:\s*(.+)$", re.MULTILINE)


def names_in(text):
    return [n for n in re.split(r"[,\s]+", text.strip()) if n]


def main():
    with open(POLICY, encoding="utf-8") as f:
        policy = json.load(f)
    problems = []
    owner = {}
    count = 0
    for section, key in SECTIONS:
        for index, rule in enumerate(policy.get(section, {}).get(key) or []):
            count += 1
            where = f"{section}.{key}[{index}]"
            name = rule.get("name") or ""
            if not name:
                problems.append(f"{where}: no name")
            elif not NAME_RE.match(name):
                problems.append(f"{where}: name {name!r} is not kebab-case")
            elif name in owner:
                problems.append(f"{where}: name {name!r} also used by {owner[name]}")
            else:
                owner[name] = where
            pattern = rule.get("pattern") or ""
            if not pattern:
                problems.append(f"{where}: no pattern")
            else:
                try:
                    re.compile(pattern)
                except re.error as exc:
                    problems.append(f"{where}: pattern does not compile: {exc}")
            reason = rule.get("reason") or ""
            if not reason:
                problems.append(f"{where}: no reason")
            elif not reason.endswith("."):
                problems.append(f"{where}: reason does not end with a full stop")
            elif len(reason) > 170:
                problems.append(f"{where}: reason is {len(reason)} chars, keep it under 170")
            elif not REMEDY_RE.search(reason):
                problems.append(f"{where}: reason gives no way forward: {reason}")

    tagged, hook_only = set(), set()
    wanted = {r["name"] for r in policy.get("bash", {}).get("ask") or [] if r.get("name")}
    have_rules = os.path.exists(RULES)
    if have_rules:
        with open(RULES, encoding="utf-8") as f:
            text = f.read()
        for group in TAG_RE.findall(text):
            tagged.update(names_in(group))
        for group in HOOK_ONLY_RE.findall(text):
            hook_only.update(names_in(group))
        for name in sorted((tagged | hook_only) - set(owner)):
            problems.append(f"{os.path.basename(RULES)}: tag {name!r} matches no rule")
        for name in sorted(wanted - tagged - hook_only):
            problems.append(f"{os.path.basename(RULES)}: no Codex rule and no hook-only note for {name!r}")
        for name in sorted(wanted & hook_only):
            print(f"note  Codex cannot express {name!r} natively; the hook only carries deny there")

    print(f"policy: {count} rules, {len(owner)} names, {len(wanted)} ask rules, {len(tagged & wanted)} mirrored in Codex")
    for problem in problems:
        print(f"FAIL  {problem}")
    print(f"{'ok' if not problems else 'failed'}: {len(problems)} problem(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
