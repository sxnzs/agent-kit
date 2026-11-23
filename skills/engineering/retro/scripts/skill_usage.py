#!/usr/bin/env python3
"""Count real skill invocations in Claude Code session transcripts.

A model call is a Skill tool call made by the assistant. A user call is a
slash command typed by the owner. Paths that merely mention a skill are not
counted. Only Claude Code transcripts are read; other hosts log skills as
plain file reads that cannot be told apart from listings.

Usage: skill_usage.py [--days N] [--projects DIR] [--skills-dir DIR]
"""

from __future__ import annotations

import argparse
import json
import re
import time
from collections import defaultdict
from pathlib import Path

COMMAND_RE = re.compile(r"<command-name>/([a-z0-9:-]+)</command-name>")


def events(path: Path):
    """Yield (kind, skill, day) for each invocation in one transcript."""
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
                        yield "user", name, day
            elif record.get("type") == "assistant" and isinstance(content, list):
                for part in content:
                    if isinstance(part, dict) and part.get("type") == "tool_use" and part.get("name") == "Skill":
                        name = (part.get("input") or {}).get("skill")
                        if isinstance(name, str):
                            yield "model", name, day


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--days", type=int, default=0, help="only transcripts modified in the last N days")
    parser.add_argument("--projects", type=Path, default=Path.home() / ".claude" / "projects")
    parser.add_argument("--skills-dir", type=Path, default=Path.home() / ".agents" / "skills")
    args = parser.parse_args()

    cutoff = time.time() - args.days * 86400 if args.days else 0
    counts: dict[str, dict[str, int]] = defaultdict(lambda: {"model": 0, "user": 0})
    last: dict[str, str] = {}
    files = 0
    days: list[str] = []
    for path in sorted(args.projects.rglob("*.jsonl")):
        if path.stat().st_mtime < cutoff:
            continue
        files += 1
        for kind, name, day in events(path):
            counts[name][kind] += 1
            last[name] = max(last.get(name, ""), day)
            if day:
                days.append(day)

    installed = sorted(p.name for p in args.skills_dir.iterdir() if (p / "SKILL.md").is_file()) if args.skills_dir.is_dir() else []
    span = f"{min(days)} to {max(days)}" if days else "no invocations"
    print(f"transcripts: {files}  invocations span: {span}")
    print(f"{'skill':<28}{'model':>6}{'user':>6}  last")
    for name in sorted(set(installed) | {n for n in counts if n in installed}, key=lambda n: (-sum(counts[n].values()), n)):
        row = counts[name]
        print(f"{name:<28}{row['model']:>6}{row['user']:>6}  {last.get(name, 'never')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
