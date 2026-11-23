#!/usr/bin/env python3
"""Keep every copy of a skill's one-line summary equal to its SKILL.md frontmatter.

The frontmatter description is the single source. Its summary (the text before
"Use when") is copied into the Codex twin, the bucket README, the top README
and the ask-kit router. Run with no arguments to rewrite the copies, or with
--check to fail when any copy has drifted.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from check_skills import discover_skills, is_quoted_yaml, parse_frontmatter, unquote_yaml

TOP_ROW_RE = re.compile(r"^\| \[([a-z0-9-]+)\]\(([^)]+)\) \| ([a-z-]+) \| (.*) \|$")
BUCKET_ROW_RE = re.compile(r"^\* \[([a-z0-9-]+)\]\(([^)]+)\): (.*)$")
ROUTER_ROW_RE = re.compile(r"^- `([a-z0-9-]+)` \((user-invoked|auto)\): (.*)$")
TWIN_ROW_RE = re.compile(r"^(\s+short_description:) (.*)$")
TOTAL_RE = re.compile(r"\*\*\d+ skills\*\*")
KIND_COUNT_RE = re.compile(r"<summary>(User|Model)-invoked skills \(\d+\)</summary>")
YAML_INDICATORS = "!&*-?|>'\"%@`#[]{},"


def summary_of(description: str) -> str:
    return re.split(r"\s+use\s+when\b", description, maxsplit=1, flags=re.IGNORECASE)[0].strip()


def yaml_scalar(value: str) -> str:
    if ": " in value or " #" in value or value.endswith(":") or value[0] in YAML_INDICATORS:
        return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'
    return value


def load_skills(skills_dir: Path) -> dict[str, tuple[str, bool, Path]]:
    skills: dict[str, tuple[str, bool, Path]] = {}
    discovered, _ = discover_skills(skills_dir)
    for _bucket, skill_dir in discovered:
        frontmatter, _ = parse_frontmatter((skill_dir / "SKILL.md").read_text(encoding="utf-8"))
        if not frontmatter or "description" not in frontmatter:
            continue
        description = frontmatter["description"]
        if is_quoted_yaml(description):
            description = unquote_yaml(description)
        is_user = frontmatter.get("disable-model-invocation") == "true"
        summary = summary_of(description)
        if summary:
            skills[skill_dir.name] = (summary, is_user, skill_dir)
    return skills


def rewrite(path: Path, transform, drift: list[str], write: bool) -> None:
    if not path.is_file():
        return
    old_lines = path.read_text(encoding="utf-8").split("\n")
    new_lines = [transform(line) for line in old_lines]
    for number, (old, new) in enumerate(zip(old_lines, new_lines), start=1):
        if old != new:
            drift.append(f"{path}:{number}: expected: {new.strip()}")
    if write and old_lines != new_lines:
        path.write_text("\n".join(new_lines), encoding="utf-8")


def require_rows(path: Path, row_re: re.Pattern[str], expected: set[str], drift: list[str]) -> None:
    """Report skills with no row in a listing and rows that name no skill."""
    if not path.is_file():
        return
    found = {m.group(1) for line in path.read_text(encoding="utf-8").split("\n") if (m := row_re.match(line))}
    for name in sorted(expected - found):
        drift.append(f"{path}: no listing row for skill {name!r} in the expected format {row_re.pattern}")
    for name in sorted(found - expected):
        drift.append(f"{path}: listing row names unknown skill {name!r}; delete it")


def sync(kit: Path, write: bool) -> list[str]:
    skills_dir = kit / "skills"
    skills = load_skills(skills_dir)
    drift: list[str] = []
    user_count = sum(1 for _, is_user, _ in skills.values() if is_user)
    counts = {"User": user_count, "Model": len(skills) - user_count}

    def top_line(line: str) -> str:
        line = TOTAL_RE.sub(f"**{len(skills)} skills**", line)
        line = KIND_COUNT_RE.sub(lambda m: f"<summary>{m.group(1)}-invoked skills ({counts[m.group(1)]})</summary>", line)
        match = TOP_ROW_RE.match(line)
        if match and match.group(1) in skills:
            name, link, bucket, _ = match.groups()
            return f"| [{name}]({link}) | {bucket} | {skills[name][0].replace('|', chr(92) + '|')} |"
        return line

    def bucket_line(line: str) -> str:
        match = BUCKET_ROW_RE.match(line)
        if match and match.group(1) in skills:
            name, link, _ = match.groups()
            return f"* [{name}]({link}): {skills[name][0]}"
        return line

    def router_line(line: str) -> str:
        match = ROUTER_ROW_RE.match(line)
        if match and match.group(1) in skills:
            name = match.group(1)
            summary, is_user, _ = skills[name]
            kind = "user-invoked" if is_user else "auto"
            return f"- `{name}` ({kind}): {summary}"
        return line

    rewrite(kit / "README.md", top_line, drift, write)
    require_rows(kit / "README.md", TOP_ROW_RE, set(skills), drift)
    for bucket_readme in sorted(skills_dir.glob("*/README.md")):
        rewrite(bucket_readme, bucket_line, drift, write)
        in_bucket = {name for name, (_, _, path) in skills.items() if path.parent == bucket_readme.parent}
        require_rows(bucket_readme, BUCKET_ROW_RE, in_bucket, drift)
    if "ask-kit" in skills:
        router = skills["ask-kit"][2] / "SKILL.md"
        rewrite(router, router_line, drift, write)
        require_rows(router, ROUTER_ROW_RE, set(skills) - {"ask-kit"}, drift)
    for summary, _, skill_dir in skills.values():
        def twin_line(line: str, summary: str = summary) -> str:
            match = TWIN_ROW_RE.match(line)
            return f"{match.group(1)} {yaml_scalar(summary)}" if match else line

        rewrite(skill_dir / "agents" / "openai.yaml", twin_line, drift, write)
    return drift


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="report drift and exit 1 without writing")
    parser.add_argument("--kit", type=Path, default=Path(__file__).resolve().parent.parent)
    args = parser.parse_args(argv)
    drift = sync(args.kit, write=not args.check)
    if args.check and drift:
        for line in drift:
            print(f"ERROR: {line}", file=sys.stderr)
        print(f"FAILED: {len(drift)} listing line(s) drifted; run scripts/sync_listings.py", file=sys.stderr)
        return 1
    unfixed = sync(args.kit, write=False) if not args.check else []
    for line in unfixed:
        print(f"ERROR: {line}", file=sys.stderr)
    if unfixed:
        return 1
    print("ok: listings match frontmatter")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
