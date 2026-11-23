#!/usr/bin/env python3
"""Count real skill invocations in Claude Code session transcripts.

A model call is a Skill tool call made by the assistant. A user call is a
slash command typed by the owner. Paths that merely mention a skill are not
counted, and a plugin prefix (`plugin:skill`) is dropped before matching.
Only Claude Code transcripts are read; other hosts log skills as plain file
reads that cannot be told apart from listings.

Usage: skill_usage.py [--days N] [--projects DIR] [--skills-dir DIR]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path

COMMAND_RE = re.compile(r"<command-name>/([a-z0-9:-]+)</command-name>")


def events(path: Path):
    """Yield (kind, skill, day, event_id) for each invocation in one transcript."""
    with path.open(encoding="utf-8", errors="replace") as handle:
        for raw in handle:
            if '"Skill"' not in raw and "<command-name>" not in raw:
                continue
            try:
                record = json.loads(raw)
            except ValueError:
                continue
            message = record.get("message")
            if not isinstance(message, dict):
                continue
            day = str(record.get("timestamp", ""))[:10]
            content = message.get("content")
            if record.get("type") == "user":
                texts = [content] if isinstance(content, str) else [
                    part.get("text", "") for part in content or [] if isinstance(part, dict) and part.get("type") == "text"
                ]
                for text in texts:
                    for name in COMMAND_RE.findall(text):
                        yield "user", name, day, f"{record.get('uuid')}:{name}"
            elif record.get("type") == "assistant" and isinstance(content, list):
                for part in content:
                    if isinstance(part, dict) and part.get("type") == "tool_use" and part.get("name") == "Skill":
                        name = (part.get("input") or {}).get("skill")
                        if isinstance(name, str):
                            yield "model", name, day, str(part.get("id"))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--days", type=int, default=0, help="only invocations from the last N days")
    parser.add_argument("--projects", type=Path, default=Path.home() / ".claude" / "projects")
    parser.add_argument("--skills-dir", type=Path, default=Path.home() / ".agents" / "skills")
    args = parser.parse_args()

    if not args.skills_dir.is_dir():
        print(f"ERROR: skills directory not found: {args.skills_dir} (pass --skills-dir)", file=sys.stderr)
        return 2
    transcripts = [p for p in sorted(args.projects.rglob("*.jsonl")) if p.is_file()] if args.projects.is_dir() else []
    if not transcripts:
        print(f"ERROR: no transcripts under {args.projects} (pass --projects); nothing can be concluded", file=sys.stderr)
        return 2

    since = (date.today() - timedelta(days=args.days)).isoformat() if args.days else ""
    installed = sorted(p.name for p in args.skills_dir.iterdir() if (p / "SKILL.md").is_file())
    counts: dict[str, dict[str, int]] = defaultdict(lambda: {"model": 0, "user": 0})
    last: dict[str, str] = {}
    seen: set[str] = set()
    days: list[str] = []
    for path in transcripts:
        for kind, raw_name, day, event_id in events(path):
            name = raw_name.rsplit(":", 1)[-1]
            if day < since or event_id in seen or name not in installed:
                continue
            seen.add(event_id)
            counts[name][kind] += 1
            last[name] = max(last.get(name, ""), day)
            days.append(day)

    span = f"{min(days)} to {max(days)}" if days else "none found"
    print(f"transcripts: {len(transcripts)}  invocations: {span}")
    print(f"{'skill':<28}{'model':>6}{'user':>6}  last")
    for name in sorted(installed, key=lambda n: (-sum(counts[n].values()), n)):
        row = counts[name]
        print(f"{name:<28}{row['model']:>6}{row['user']:>6}  {last.get(name, 'never')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
