#!/usr/bin/env python3
"""Merge or unmerge a JSON fragment into a JSON config file, in place.

  jsonmerge.py merge   TARGET FRAGMENT [--dry-run]
  jsonmerge.py unmerge TARGET FRAGMENT [--dry-run]

merge:   dicts merge recursively, lists gain fragment items not already present,
         scalars are set only when the key is missing (your values win).
unmerge: removes exactly what merge added (list items equal to fragment items,
         keys whose value equals the fragment value), then drops empty containers.
Keys starting with "$" or "_" in the fragment are ignored.
A backup TARGET.bak.agent-kit is written before the first change.
"""
import json
import os
import shutil
import sys


def merge(dst, frag):
    for k, v in frag.items():
        if k.startswith(("$", "_")):
            continue
        if k not in dst:
            dst[k] = v
        elif isinstance(dst[k], dict) and isinstance(v, dict):
            merge(dst[k], v)
        elif isinstance(dst[k], list) and isinstance(v, list):
            for item in v:
                if item not in dst[k]:
                    dst[k].append(item)
        # scalar already set by the user: keep theirs


def unmerge(dst, frag):
    for k, v in frag.items():
        if k not in dst or k.startswith(("$", "_")):
            continue
        if isinstance(dst[k], dict) and isinstance(v, dict):
            unmerge(dst[k], v)
            if not dst[k]:
                del dst[k]
        elif isinstance(dst[k], list) and isinstance(v, list):
            dst[k] = [i for i in dst[k] if i not in v]
            if not dst[k]:
                del dst[k]
        elif dst[k] == v:
            del dst[k]


def main():
    if len(sys.argv) < 4 or sys.argv[1] not in ("merge", "unmerge"):
        print(__doc__)
        return 2
    mode, target, fragment = sys.argv[1:4]
    dry = "--dry-run" in sys.argv
    with open(fragment, encoding="utf-8") as f:
        frag = json.load(f)
    data = {}
    if os.path.exists(target):
        with open(target, encoding="utf-8") as f:
            text = f.read().strip()
        data = json.loads(text) if text else {}
    before = json.dumps(data, sort_keys=True)
    (merge if mode == "merge" else unmerge)(data, frag)
    if json.dumps(data, sort_keys=True) == before:
        print(f"  unchanged  {target}")
        return 0
    if dry:
        print(f"  would {mode:7} {target}")
        return 0
    if os.path.exists(target) and not os.path.exists(target + ".bak.agent-kit"):
        shutil.copy2(target, target + ".bak.agent-kit")
    os.makedirs(os.path.dirname(target) or ".", exist_ok=True)
    with open(target, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print(f"  {mode}d    {target}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
