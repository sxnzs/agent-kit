#!/usr/bin/env python3
"""Deterministic Layer 2 validator for ~/agent-kit/skills.

Checks portable frontmatter, body length, Codex twin files, reference link integrity,
stale frontmatter inside references/, ghost archived skill names, and stray files.
Zero third-party dependencies.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

BUCKETS = ("engineering", "productivity", "in-progress")
ALLOWED_FM_KEYS = frozenset({"name", "description", "disable-model-invocation", "argument-hint"})
YAML_INDICATOR_CHARS = frozenset("&*!|>'\"%@`[{?:,-#")
SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
MULTI_SENTENCE_RE = re.compile(r"[.!?]\s+[A-Z]")
MD_LINK_RE = re.compile(r"!?\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
FENCE_RE = re.compile(r"^\s*(`{3,}|~{3,})")
INLINE_CODE_RE = re.compile(r"`([^`]+)`")
SKILL_CALL_RE = re.compile(r'Call the Skill tool with "([^"]+)"')
TELL_USER_RUN_RE = re.compile(r"tell the user to run\s+the\s+`?([a-z0-9-]+)`?\s+skill", re.IGNORECASE)
BOLD_SKILL_REF_RE = re.compile(r"\b(?:suggest|run|with)\s+\*\*([a-z0-9-]+)\*\*")
TELL_USER_SLASH_RE = re.compile(r"tell the user to run\s+`?/([a-z0-9-]+)`?", re.IGNORECASE)
HOME_SKILL_PATH_RE = re.compile(r"~/\.(?:agents|claude)/skills/([a-z0-9-]+)(?:/|$|\s)")
REL_SKILL_SUBDIR_RE = re.compile(r"(?<![a-z0-9_/-])([a-z0-9-]+)/(?:references|scripts|assets)/")

# Skills retired or absorbed into references/ during the 26->10 consolidation.
RETIRED_SKILLS = (
    "motion-design",
    "notion-workspace",
    "terminal-look",
    "visual-design",
    "write-swift",
)

GHOST_SKILL_RE = re.compile(
    r"(?:\*\*(" + "|".join(RETIRED_SKILLS) + r")\*\*"
    r"|\b(?:use|run|suggest)\s+(" + "|".join(RETIRED_SKILLS) + r")\b)",
    re.IGNORECASE,
)


def strip_fenced_blocks(text: str) -> list[tuple[int, str]]:
    """Return (1-based line_no, line) excluding fenced code blocks."""
    out: list[tuple[int, str]] = []
    in_fence: str | None = None
    for idx, line in enumerate(text.splitlines(), start=1):
        m = FENCE_RE.match(line)
        if m:
            ch = m.group(1)[0]
            if in_fence is None:
                in_fence = ch
            elif in_fence == ch:
                in_fence = None
            continue
        if in_fence is None:
            out.append((idx, line))
    return out


def is_quoted_yaml(val: str) -> bool:
    return len(val) >= 2 and ((val[0] == '"' and val[-1] == '"') or (val[0] == "'" and val[-1] == "'"))


def unquote_yaml(val: str) -> str:
    if len(val) >= 2 and val[0] == '"' and val[-1] == '"':
        return val[1:-1].replace('\\"', '"').replace("\\\\", "\\")
    if len(val) >= 2 and val[0] == "'" and val[-1] == "'":
        return val[1:-1].replace("''", "'")
    return val


def parse_openai_yaml(path: Path) -> dict[str, dict[str, str]] | None:
    """Parse minimal two-level agents/openai.yaml (interface, policy)."""
    data: dict[str, dict[str, str]] = {}
    section: str | None = None
    for raw in path.read_text(encoding="utf-8").splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        if not raw[0].isspace():
            if not raw.rstrip().endswith(":"):
                return None
            section = raw.rstrip()[:-1].strip()
            data.setdefault(section, {})
        else:
            if section is None or ":" not in raw:
                return None
            key, val = raw.strip().split(":", 1)
            data[section][key.strip()] = unquote_yaml(val.strip())
    return data


def parse_frontmatter(text: str) -> tuple[dict[str, str] | None, int]:
    """Parse flat YAML frontmatter and return (mapping, body_line_count)."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None, len(lines)
    end_idx = None
    for idx in range(1, len(lines)):
        if lines[idx].strip() == "---":
            end_idx = idx
            break
    if end_idx is None:
        return None, len(lines)

    data: dict[str, str] = {}
    for raw in lines[1:end_idx]:
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        if ":" not in raw:
            return None, len(lines) - end_idx - 1
        key, val = raw.split(":", 1)
        data[key.strip()] = val.strip()
    return data, len(lines) - end_idx - 1


def check_links(
    md_path: Path,
    skill_dir: Path,
    errors: list[str],
    linked_targets: set[Path] | None = None,
) -> None:
    text = md_path.read_text(encoding="utf-8")
    skill_root = skill_dir.resolve()
    for line_no, line in strip_fenced_blocks(text):
        for match in MD_LINK_RE.finditer(line):
            raw_target = match.group(1)
            if raw_target.startswith(("http://", "https://", "mailto:", "file://", "#")):
                continue
            target_part = raw_target.split("#", 1)[0]
            if not target_part:
                continue
            resolved = (md_path.parent / target_part).resolve()
            if not resolved.is_relative_to(skill_root):
                errors.append(f"{md_path}:{line_no}: link leaves skill folder -> {raw_target}")
            elif not resolved.exists():
                errors.append(f"{md_path}:{line_no}: broken link -> {raw_target}")
            elif linked_targets is not None:
                linked_targets.add(resolved)


def check_cross_skill_refs(
    md_path: Path,
    skill_dir: Path,
    skill_kinds: dict[str, bool],
    errors: list[str],
) -> None:
    text = md_path.read_text(encoding="utf-8")
    own_name = skill_dir.name
    skill_root = skill_dir.resolve()
    for line_no, line in strip_fenced_blocks(text):
        for code_match in INLINE_CODE_RE.finditer(line):
            code = code_match.group(1)
            for m in HOME_SKILL_PATH_RE.finditer(code):
                target = m.group(1)
                if target != own_name:
                    errors.append(f"{md_path}:{line_no}: backticked path points into another skill {target!r}")
            for m in REL_SKILL_SUBDIR_RE.finditer(code):
                target = m.group(1)
                if target != own_name and target in skill_kinds:
                    errors.append(f"{md_path}:{line_no}: backticked path points into another skill {target!r}")
            if "../" in code and not code.startswith(("http://", "https://")):
                token = code.split()[0]
                if token.startswith("../"):
                    resolved = (md_path.parent / token).resolve()
                    if not resolved.is_relative_to(skill_root):
                        errors.append(f"{md_path}:{line_no}: backticked path leaves skill folder -> {token}")

        cleaned = INLINE_CODE_RE.sub("", line)
        for m in SKILL_CALL_RE.finditer(cleaned):
            target = m.group(1)
            if target not in skill_kinds:
                errors.append(f"{md_path}:{line_no}: Skill tool call targets unknown skill {target!r}")
            elif skill_kinds[target]:
                errors.append(f"{md_path}:{line_no}: Skill tool call targets user-invoked skill {target!r}")

        for m in TELL_USER_RUN_RE.finditer(line):
            target = m.group(1)
            if target not in skill_kinds:
                errors.append(
                    f"{md_path}:{line_no}: 'tell the user to run the {target} skill' names unknown skill {target!r}"
                )

        for m in BOLD_SKILL_REF_RE.finditer(cleaned):
            target = m.group(1)
            if target not in skill_kinds:
                errors.append(f"{md_path}:{line_no}: bold skill mention names unknown skill {target!r}")

        for m in TELL_USER_SLASH_RE.finditer(line):
            target = m.group(1)
            errors.append(
                f"{md_path}:{line_no}: use host-neutral 'tell the user to run the {target} skill' instead of '/{target}'"
            )


def check_bucket_readmes_and_router(
    skills_dir: Path,
    discovered: list[tuple[str, Path]],
    skill_kinds: dict[str, bool],
    errors: list[str],
) -> None:
    by_bucket: dict[str, list[Path]] = {}
    ask_kit_md: Path | None = None
    for bucket, skill_dir in discovered:
        by_bucket.setdefault(bucket, []).append(skill_dir)
        if skill_dir.name == "ask-kit":
            ask_kit_md = skill_dir / "SKILL.md"

    for bucket, skill_dirs in sorted(by_bucket.items()):
        readme = skills_dir / bucket / "README.md"
        if not readme.is_file():
            errors.append(f"{skills_dir / bucket}: missing README.md")
            continue
        section: str | None = None
        listed: dict[str, set[str]] = {"user": set(), "model": set()}
        for _line_no, line in strip_fenced_blocks(readme.read_text(encoding="utf-8")):
            stripped = line.strip()
            if stripped.startswith("#"):
                heading = stripped.lstrip("#").strip().lower()
                if heading == "user-invoked":
                    section = "user"
                elif heading == "model-invoked":
                    section = "model"
                else:
                    section = None
                continue
            if section is not None:
                for m in MD_LINK_RE.finditer(line):
                    target = m.group(1)
                    if target.endswith("/SKILL.md"):
                        listed[section].add(target[: -len("/SKILL.md")])

        for skill_dir in skill_dirs:
            name = skill_dir.name
            expected_sec = "user" if skill_kinds.get(name, False) else "model"
            other_sec = "model" if expected_sec == "user" else "user"
            if name not in listed[expected_sec]:
                heading_label = "User-invoked" if expected_sec == "user" else "Model-invoked"
                errors.append(
                    f"{readme}: skill {name!r} missing under '{heading_label}' (expected link to {name}/SKILL.md)"
                )
            if name in listed[other_sec]:
                wrong_label = "User-invoked" if other_sec == "user" else "Model-invoked"
                errors.append(f"{readme}: skill {name!r} listed under wrong heading '{wrong_label}'")

    if ask_kit_md is not None and ask_kit_md.is_file():
        ask_text = ask_kit_md.read_text(encoding="utf-8")
        if SKILL_CALL_RE.search(ask_text):
            errors.append(f"{ask_kit_md}: router must name skills and never call the Skill tool")
        for name, is_user in sorted(skill_kinds.items()):
            if name == "ask-kit":
                continue
            if not re.search(rf"`{re.escape(name)}`", ask_text):
                kind_label = "user-invoked" if is_user else "model-invoked"
                errors.append(f"{ask_kit_md}: {kind_label} skill '`{name}`' not listed in ask-kit")


def check_ghost_skills(md_path: Path, errors: list[str]) -> None:
    text = md_path.read_text(encoding="utf-8")
    for line_no, line in strip_fenced_blocks(text):
        cleaned = INLINE_CODE_RE.sub("", line)
        for match in GHOST_SKILL_RE.finditer(cleaned):
            token = match.group(1) or match.group(2)
            # Allow prose mentioning "run next" or "use next" in ordinary English,
            # only flag bold **next** or retired multi-word/distinct skill names.
            if token.lower() in ("next", "ship", "teach", "grill", "handoff") and not match.group(0).startswith("**"):
                continue
            errors.append(
                f"{md_path}:{line_no}: stale standalone skill reference {match.group(0)!r}"
            )


def discover_skills(skills_dir: Path) -> tuple[list[tuple[str, Path]], list[str]]:
    """Discover skills at skills/<bucket>/<name>/ and detect duplicates."""
    errors: list[str] = []
    discovered: list[tuple[str, Path]] = []
    seen: dict[str, Path] = {}

    if not skills_dir.is_dir():
        return [], [f"skills directory not found: {skills_dir}"]

    bucket_dirs = sorted(p for p in skills_dir.iterdir() if p.is_dir() and not p.name.startswith("."))
    for bucket_dir in bucket_dirs:
        if bucket_dir.name not in BUCKETS:
            errors.append(f"unknown skill bucket: {bucket_dir}")
            continue
        for skill_dir in sorted(p for p in bucket_dir.iterdir() if p.is_dir() and not p.name.startswith(".")):
            if skill_dir.name in seen:
                errors.append(f"duplicate skill name {skill_dir.name!r}: {seen[skill_dir.name]} and {skill_dir}")
            else:
                seen[skill_dir.name] = skill_dir
            discovered.append((bucket_dir.name, skill_dir))

    if not discovered and not errors:
        errors.append(f"no skill directories found in {skills_dir}")

    return discovered, errors


def validate_skills(skills_dir: Path, check_symlinks: Path | None) -> list[str]:
    discovered, errors = discover_skills(skills_dir)
    if not skills_dir.is_dir():
        return errors

    for stray in skills_dir.rglob("*"):
        if stray.name in ("__pycache__", ".DS_Store", ".ruff_cache"):
            errors.append(f"stray artifact in skills tree: {stray}")

    skill_kinds: dict[str, bool] = {}
    for _bucket, skill_dir in discovered:
        skill_md = skill_dir / "SKILL.md"
        if skill_md.is_file():
            fm, _ = parse_frontmatter(skill_md.read_text(encoding="utf-8"))
            skill_kinds[skill_dir.name] = bool(fm and fm.get("disable-model-invocation") == "true")

    for _bucket, skill_dir in discovered:
        skill_md = skill_dir / "SKILL.md"
        if not skill_md.is_file():
            errors.append(f"{skill_dir}: missing SKILL.md")
            continue

        text = skill_md.read_text(encoding="utf-8")
        fm, body_lines = parse_frontmatter(text)
        is_user_invoked = False
        if fm is None:
            errors.append(f"{skill_md}: missing or malformed YAML frontmatter")
        else:
            keys = set(fm.keys())
            unknown_keys = sorted(keys - ALLOWED_FM_KEYS)
            missing_keys = sorted({"name", "description"} - keys)
            if unknown_keys or missing_keys:
                errors.append(
                    f"{skill_md}: invalid frontmatter keys (unknown={unknown_keys}, missing={missing_keys}); "
                    f"allowed keys are {sorted(ALLOWED_FM_KEYS)}"
                )
            for key, raw_val in fm.items():
                if not is_quoted_yaml(raw_val):
                    if ": " in raw_val or (raw_val and raw_val[0] in YAML_INDICATOR_CHARS):
                        errors.append(
                            f"{skill_md}: frontmatter {key!r} must be quoted (contains ': ' or starts with YAML indicator)"
                        )
            name_val = fm.get("name", "")
            if is_quoted_yaml(name_val):
                errors.append(f"{skill_md}: unquote frontmatter name ({name_val})")
                name_val = unquote_yaml(name_val)
            if name_val != skill_dir.name:
                errors.append(f"{skill_md}: name {name_val!r} != folder {skill_dir.name!r}")
            if not SLUG_RE.match(name_val) or len(name_val) > 64:
                errors.append(
                    f"{skill_md}: invalid skill slug {name_val!r} "
                    "(lowercase letters, digits, single hyphens, at most 64 chars)"
                )

            dmi_raw = fm.get("disable-model-invocation")
            if dmi_raw is not None:
                if dmi_raw != "true":
                    errors.append(
                        f"{skill_md}: disable-model-invocation must be true (omit key for model-invoked skills)"
                    )
                else:
                    is_user_invoked = True

            desc = unquote_yaml(fm.get("description", ""))
            if not desc:
                errors.append(f"{skill_md}: empty description")
            elif is_user_invoked:
                if len(desc) > 160:
                    errors.append(f"{skill_md}: user-invoked description exceeds 160 chars ({len(desc)})")
                if "use when" in desc.lower():
                    errors.append(f"{skill_md}: user-invoked description must not contain 'Use when'")
                if MULTI_SENTENCE_RE.search(desc):
                    errors.append(f"{skill_md}: user-invoked description must be one sentence")
            else:
                if len(desc) > 1024:
                    errors.append(f"{skill_md}: description exceeds 1024 chars ({len(desc)})")
                if "use when" not in desc.lower():
                    errors.append(f"{skill_md}: model-invoked description must include 'Use when'")

        openai_yaml = skill_dir / "agents" / "openai.yaml"
        if not openai_yaml.is_file():
            errors.append(f"{skill_dir}: missing agents/openai.yaml")
        else:
            twin = parse_openai_yaml(openai_yaml)
            if twin is None:
                errors.append(f"{openai_yaml}: malformed YAML")
            else:
                iface = twin.get("interface", {})
                if not iface.get("display_name"):
                    errors.append(f"{openai_yaml}: missing interface.display_name")
                if not iface.get("short_description"):
                    errors.append(f"{openai_yaml}: missing interface.short_description")
                allow_implicit = twin.get("policy", {}).get("allow_implicit_invocation")
                if is_user_invoked and allow_implicit != "false":
                    errors.append(
                        f"{openai_yaml}: user-invoked skill must set policy.allow_implicit_invocation: false"
                    )
                if not is_user_invoked and allow_implicit == "false":
                    errors.append(
                        f"{openai_yaml}: model-invoked skill must not set policy.allow_implicit_invocation: false"
                    )

        if body_lines >= 500:
            errors.append(f"{skill_md}: body has {body_lines} lines (limit < 500)")

        adjacency: dict[Path, set[Path]] = {}
        ref_md_files: list[Path] = []
        for md_file in sorted(skill_dir.rglob("*.md")):
            targets: set[Path] = set()
            check_links(md_file, skill_dir, errors, targets)
            adjacency[md_file.resolve()] = targets
            check_ghost_skills(md_file, errors)
            check_cross_skill_refs(md_file, skill_dir, skill_kinds, errors)
            if "references" in md_file.relative_to(skill_dir).parts:
                ref_md_files.append(md_file)
                ref_fm, _ = parse_frontmatter(md_file.read_text(encoding="utf-8"))
                if ref_fm is not None:
                    errors.append(f"{md_file}: reference file should not carry skill YAML frontmatter")

        reachable: set[Path] = set()
        queue: list[Path] = [skill_md.resolve()]
        while queue:
            current = queue.pop()
            if current in reachable:
                continue
            reachable.add(current)
            for nxt in adjacency.get(current, ()):
                if nxt not in reachable:
                    queue.append(nxt)

        for ref_md in ref_md_files:
            if ref_md.resolve() not in reachable:
                errors.append(f"{ref_md}: unreachable markdown file under references/")

    check_bucket_readmes_and_router(skills_dir, discovered, skill_kinds, errors)

    if check_symlinks is not None:
        if not check_symlinks.is_dir():
            errors.append(f"symlink directory not found: {check_symlinks}")
        else:
            expected = {d.name: d.resolve() for bucket, d in discovered if bucket != "in-progress"}
            for name, target in expected.items():
                link = check_symlinks / name
                if not link.exists():
                    errors.append(f"missing link in {check_symlinks}: {name}")
                elif link.resolve() != target:
                    errors.append(f"link mismatch: {link} -> {link.resolve()} (expected {target})")
            for entry in sorted(check_symlinks.iterdir()):
                if entry.is_symlink() and not entry.exists():
                    errors.append(f"broken symlink in {check_symlinks}: {entry}")

    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate agent-kit skills library.")
    parser.add_argument(
        "--skills-dir",
        type=Path,
        default=Path(__file__).resolve().parent.parent / "skills",
        help="Path to skills directory.",
    )
    parser.add_argument(
        "--check-links",
        type=Path,
        default=None,
        help="Optional directory (e.g. ~/.agents/skills) to verify skill symlinks against.",
    )
    args = parser.parse_args(argv)

    discovered, _ = discover_skills(args.skills_dir)
    errors = validate_skills(args.skills_dir, args.check_links)
    skill_count = len(discovered)
    if errors:
        for err in errors:
            print(f"ERROR: {err}", file=sys.stderr)
        print(f"FAILED: {len(errors)} error(s) across {skill_count} skills", file=sys.stderr)
        return 1

    print(f"OK: {skill_count}/{skill_count} skills valid, 0 errors")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
