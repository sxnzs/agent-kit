#!/usr/bin/env python3
"""Enforce top-level architectural import boundaries across Amnesiac Agents.

Layer rules:
  guard/                  -> stdlib / node builtins only (no cross-layer imports)
  adapters/<host>/        -> may import guard/ only; no other host or repo layer
  scripts/                -> stdlib + sibling scripts/ modules only
  skills/<bucket>/<name>/ -> stdlib + same-skill modules only
  bin/                    -> standalone; no imports from scripts/, skills/, adapters/
"""

from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

JS_IMPORT_RE = re.compile(
    r"""(?:\bimport\s+(?:[^'"]*?\s+from\s+)?|\bexport\s+[^'"]*?\s+from\s+|\bimport\s*\(|\brequire\s*\()\s*['"]([^'"]+)['"]"""
)
PY_LAYERS = {"guard", "adapters", "scripts", "skills", "bin"}
CODE_SUFFIXES = {".py", ".js", ".mjs", ".ts", ".sh"}
CODE_NAMES = {"verify", "cm"}
ESCAPE_HATCH_RE = re.compile(
    r"(?:#\s*noqa\b|#\s*type:\s*ignore\b|eslint-disable|@ts-ignore\b|@ts-expect-error\b|shellcheck\s+disable=)"
)


def _layer_of(rel: Path) -> tuple[str, str | None]:
    parts = rel.parts
    if not parts:
        return ("root", None)
    top = parts[0]
    if top == "adapters" and len(parts) >= 2:
        return ("adapters", parts[1])
    if top == "skills" and len(parts) >= 3:
        return ("skills", f"{parts[1]}/{parts[2]}")
    if top in PY_LAYERS:
        return (top, None)
    return ("other", None)


def _check_target_layer(
    src_rel: Path,
    src_layer: str,
    src_scope: str | None,
    target_layer: str,
    target_scope: str | None,
    spec: str,
    lineno: int,
) -> str | None:
    if target_layer not in PY_LAYERS:
        return None
    if src_layer == "guard":
        if target_layer != "guard":
            return (
                f"{src_rel}:{lineno}: illegal import {spec!r} from guard/ into {target_layer}/. "
                "guard/ must stay self-contained (stdlib/node builtins only)."
            )
    elif src_layer == "adapters":
        if target_layer == "guard":
            return None
        if target_layer == "adapters" and target_scope == src_scope:
            return None
        return (
            f"{src_rel}:{lineno}: illegal import {spec!r} from adapters/{src_scope}/ into {target_layer}/. "
            "Adapters may only reference guard/ or their own host directory."
        )
    elif src_layer == "scripts":
        if target_layer != "scripts":
            return (
                f"{src_rel}:{lineno}: illegal import {spec!r} from scripts/ into {target_layer}/. "
                "Keep repo tooling decoupled; read other layers as data, not code imports."
            )
    elif src_layer == "skills":
        if target_layer == "skills" and target_scope == src_scope:
            return None
        return (
            f"{src_rel}:{lineno}: illegal import {spec!r} from skills/{src_scope}/ into {target_layer}/. "
            "Skills must be self-contained; duplicate tiny helpers or move shared logic into the same skill."
        )
    elif src_layer == "bin" and target_layer in {"scripts", "skills", "adapters"}:
        return (
            f"{src_rel}:{lineno}: illegal import {spec!r} from bin/ into {target_layer}/. "
            "CLI helpers in bin/ must stay standalone."
        )
    return None


def _check_python_file(root: Path, path: Path) -> list[str]:
    rel = path.relative_to(root)
    src_layer, src_scope = _layer_of(rel)
    if src_layer not in PY_LAYERS:
        return []
    text = path.read_text(encoding="utf-8")
    tree = ast.parse(text, filename=str(rel))
    errors: list[str] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                top = alias.name.split(".")[0]
                if top in PY_LAYERS:
                    err = _check_target_layer(
                        rel, src_layer, src_scope, top, None, alias.name, node.lineno
                    )
                    if err:
                        errors.append(err)
        elif isinstance(node, ast.ImportFrom):
            if node.level > 0:
                base = rel.parent
                for _ in range(node.level - 1):
                    base = base.parent
                target_rel = base / (node.module.replace(".", "/") if node.module else "")
                try:
                    resolved = (root / target_rel).resolve().relative_to(root.resolve())
                except ValueError:
                    errors.append(
                        f"{rel}:{node.lineno}: relative import escapes repository root."
                    )
                    continue
                t_layer, t_scope = _layer_of(resolved)
                spec = "." * node.level + (node.module or "")
                err = _check_target_layer(
                    rel, src_layer, src_scope, t_layer, t_scope, spec, node.lineno
                )
                if err:
                    errors.append(err)
            elif node.module:
                top = node.module.split(".")[0]
                if top in PY_LAYERS:
                    err = _check_target_layer(
                        rel, src_layer, src_scope, top, None, node.module, node.lineno
                    )
                    if err:
                        errors.append(err)
    return errors


def _check_js_file(root: Path, path: Path) -> list[str]:
    rel = path.relative_to(root)
    src_layer, src_scope = _layer_of(rel)
    if src_layer not in PY_LAYERS:
        return []
    text = path.read_text(encoding="utf-8")
    errors: list[str] = []
    for lineno, line in enumerate(text.splitlines(), start=1):
        stripped = line.lstrip()
        if stripped.startswith("//"):
            continue
        for match in JS_IMPORT_RE.finditer(line):
            spec = match.group(1)
            if not spec.startswith("."):
                continue
            try:
                resolved = (path.parent / spec).resolve().relative_to(root.resolve())
            except ValueError:
                errors.append(
                    f"{rel}:{lineno}: relative import {spec!r} escapes repository root."
                )
                continue
            t_layer, t_scope = _layer_of(resolved)
            err = _check_target_layer(
                rel, src_layer, src_scope, t_layer, t_scope, spec, lineno
            )
            if err:
                errors.append(err)
    return errors


def check_boundaries(root: Path = ROOT) -> list[str]:
    errors: list[str] = []
    for path in sorted(root.rglob("*")):
        if ".git" in path.parts or not path.is_file():
            continue
        if path.suffix == ".py":
            errors.extend(_check_python_file(root, path))
        elif path.suffix in {".js", ".mjs", ".ts"}:
            errors.extend(_check_js_file(root, path))
    return errors


def check_escape_hatches(root: Path = ROOT) -> list[str]:
    errors: list[str] = []
    for path in sorted(root.rglob("*")):
        if ".git" in path.parts or not path.is_file():
            continue
        if path.suffix not in CODE_SUFFIXES and path.name not in CODE_NAMES:
            continue
        rel = path.relative_to(root)
        if rel == Path("scripts/check_boundaries.py") or rel == Path("scripts/test_check_boundaries.py"):
            continue
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            match = ESCAPE_HATCH_RE.search(line)
            if match:
                errors.append(
                    f"{rel}:{lineno}: inline lint-disable pragma {match.group(0)!r} is forbidden. "
                    "Fix the underlying rule violation instead of suppressing it."
                )
    return errors


def main() -> int:
    errors = check_boundaries(ROOT) + check_escape_hatches(ROOT)
    if errors:
        for err in errors:
            print(f"FAIL  {err}", file=sys.stderr)
        print(f"boundaries: {len(errors)} violation(s)", file=sys.stderr)
        return 1
    print("ok: 0 architectural boundary or escape-hatch violations")
    return 0


if __name__ == "__main__":
    sys.exit(main())
