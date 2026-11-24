#!/usr/bin/env python3
"""Deterministic prose checker for AI-writing tells and neutral LatAm Spanish.

Zero third-party dependencies. Ignores YAML frontmatter, fenced code blocks,
inline code, and URLs while preserving exact 1-based line numbers.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

FENCE_RE = re.compile(r"^\s*(`{3,}|~{3,})")
INLINE_CODE_RE = re.compile(r"`[^`\n]+`")
URL_RE = re.compile(r"https?://\S+")
MD_LINK_TARGET_RE = re.compile(r"\]\([^)\n]+\)")
LIST_PREFIX_RE = re.compile(r"^\s*(?:[-*+]|\d+\.)\s+")
HEADING_RE = re.compile(r"^\s*#{1,6}\s+")
TABLE_ROW_RE = re.compile(r"^\s*\|")
WORD_RE = re.compile(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ0-9]+")

SPANISH_MARKERS = re.compile(
    r"\b(?:el|la|los|las|que|para|con|por|una|uno|pero|como|más|también|porque|cuando|donde|sobre|entre)\b",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class Rule:
    code: str
    severity: str  # "ERROR" or "WARN"
    lang: str  # "any", "es", "en"
    pattern: re.Pattern[str]
    hint: str


RULES: tuple[Rule, ...] = (
    # Universal formatting / structure tells
    Rule(
        code="dash-in-prose",
        severity="ERROR",
        lang="any",
        pattern=re.compile(r"[\u2014\u2013]|(?<=\S)\s-\s(?=\S)"),
        hint="replace dash with a period or comma",
    ),
    Rule(
        code="throat-clearing",
        severity="WARN",
        lang="any",
        pattern=re.compile(
            r"^\s*(?:¡?\s*(?:claro|por supuesto|excelente pregunta|buena pregunta|con gusto)\b"
            r"|(?:certainly|of course|great question|happy to help|sure,\s+i\s+can)\b)",
            re.IGNORECASE,
        ),
        hint="cut preamble and start with the answer",
    ),
    Rule(
        code="contrast-template",
        severity="WARN",
        lang="any",
        pattern=re.compile(
            r"\b(?:no\s+(?:es|son|solo)\s+[^.,;:\n]{2,45},\s*sino\b"
            r"|it['\u2019]s\s+not\s+[^.,;:\n]{2,45},\s*it['\u2019]s\b"
            r"|not\s+just\s+[^.,;:\n]{2,45},\s*but\b)",
            re.IGNORECASE,
        ),
        hint="state what it is directly instead of a staged contrast",
    ),
    # Neutral Latin American Spanish lexicon & calques
    Rule(
        code="es-spain-lexicon",
        severity="ERROR",
        lang="es",
        pattern=re.compile(
            r"\b(?:ordenador(?:es)?|fichero(?:s)?|coche(?:s)?|ascensor(?:es)?|t[íi]o|guay|mola|coger)\b",
            re.IGNORECASE,
        ),
        hint="use neutral LatAm Spanish (computadora, archivo, carro, elevador)",
    ),
    Rule(
        code="es-spain-soft",
        severity="WARN",
        lang="es",
        pattern=re.compile(
            r"\b(?:m[óo]vil(?:es)?|vale(?!\s+la\s+pena))\b",
            re.IGNORECASE,
        ),
        hint="prefer celular (for phones) or drop Spain filler 'vale'",
    ),
    Rule(
        code="es-calque",
        severity="ERROR",
        lang="es",
        pattern=re.compile(
            r"\b(?:hace\s+sentido|en\s+orden\s+de|accesar|cabe\s+destacar"
            r"|es\s+importante\s+se[ñn]alar|jugar\s+un\s+papel(?:\s+clave)?"
            r"|en\s+[úu]ltima\s+instancia|a\s+trav[ée]s\s+de\s+la\s+utilizaci[óo]n)\b",
            re.IGNORECASE,
        ),
        hint="replace English calque or filler phrase with direct Spanish",
    ),
    Rule(
        code="es-ai-filler",
        severity="WARN",
        lang="es",
        pattern=re.compile(
            r"\b(?:en\s+esencia|en\s+resumen,|en\s+conclusi[óo]n,|lo\s+cual\s+permite"
            r"|impulsar(?:[áa]n?)?|fomentar(?:[áa]n?)?|aprovechar\s+al\s+m[áa]ximo)\b",
            re.IGNORECASE,
        ),
        hint="replace stock filler with a concrete verb or cut it",
    ),
    # English AI-writing tells
    Rule(
        code="en-ai-tell",
        severity="WARN",
        lang="en",
        pattern=re.compile(
            r"\b(?:delve(?:s|d|ing)?|foster(?:s|ed|ing)?|it['\u2019]s\s+worth\s+noting"
            r"|importantly,|in\s+conclusion,|bottom\s+line:|genuinely)\b",
            re.IGNORECASE,
        ),
        hint="replace stock wording with concrete claim",
    ),
)


@dataclass(frozen=True)
class Finding:
    path: str
    line: int
    severity: str
    code: str
    snippet: str
    hint: str

    def format(self) -> str:
        return f"{self.path}:{self.line}: [{self.severity}] {self.code}: {self.snippet!r} -> {self.hint}"


def strip_non_prose_lines(text: str) -> list[tuple[int, str]]:
    """Return (1-based line_no, cleaned_prose) skipping frontmatter and code fences."""
    lines = text.splitlines()
    out: list[tuple[int, str]] = []
    in_fence: str | None = None
    in_frontmatter = False

    for idx, raw in enumerate(lines, start=1):
        if idx == 1 and raw.strip() == "---":
            in_frontmatter = True
            continue
        if in_frontmatter:
            if raw.strip() in ("---", "..."):
                in_frontmatter = False
            continue

        fence_match = FENCE_RE.match(raw)
        if fence_match:
            marker = fence_match.group(1)[0]
            if in_fence is None:
                in_fence = marker
            elif in_fence == marker:
                in_fence = None
            continue
        if in_fence is not None:
            continue

        cleaned = INLINE_CODE_RE.sub(" ", raw)
        cleaned = MD_LINK_TARGET_RE.sub("]", cleaned)
        cleaned = URL_RE.sub(" ", cleaned)
        out.append((idx, cleaned))
    return out


def detect_language(prose_lines: list[tuple[int, str]]) -> str:
    joined = " ".join(line for _, line in prose_lines)
    words = WORD_RE.findall(joined)
    if not words:
        return "en"
    es_hits = len(SPANISH_MARKERS.findall(joined))
    has_es_chars = any(ch in joined for ch in "áéíóúüñÁÉÍÓÚÜÑ¿¡")
    if has_es_chars or (es_hits / len(words)) >= 0.05:
        return "es"
    return "en"


def check_text(text: str, path: str, lang: str = "auto", max_sentence_words: int = 38) -> list[Finding]:
    prose_lines = strip_non_prose_lines(text)
    resolved_lang = detect_language(prose_lines) if lang == "auto" else lang
    findings: list[Finding] = []

    for line_no, raw_line in prose_lines:
        if TABLE_ROW_RE.match(raw_line):
            continue
        line = LIST_PREFIX_RE.sub("", raw_line)
        if not line.strip():
            continue

        for rule in RULES:
            if rule.lang not in ("any", resolved_lang):
                continue
            for match in rule.pattern.finditer(line):
                findings.append(
                    Finding(
                        path=path,
                        line=line_no,
                        severity=rule.severity,
                        code=rule.code,
                        snippet=match.group(0).strip(),
                        hint=rule.hint,
                    )
                )

        if not HEADING_RE.match(raw_line):
            for sentence in re.split(r"[.!?¿¡]+", line):
                words = WORD_RE.findall(sentence)
                if len(words) > max_sentence_words:
                    findings.append(
                        Finding(
                            path=path,
                            line=line_no,
                            severity="WARN",
                            code="long-sentence",
                            snippet=f"{len(words)} words",
                            hint=f"split sentence past {max_sentence_words} words",
                        )
                    )

    return findings


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check prose for AI-writing tells, dashes, and LatAm Spanish calques."
    )
    parser.add_argument(
        "files",
        nargs="*",
        help="Markdown or text files to check (reads stdin when omitted or '-').",
    )
    parser.add_argument(
        "--lang",
        choices=("auto", "es", "en"),
        default="auto",
        help="Language ruleset (default: auto).",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit non-zero on WARN findings as well as ERROR findings.",
    )
    parser.add_argument(
        "--max-words",
        type=int,
        default=38,
        help="Warn when a single sentence exceeds this many words (default: 38).",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    targets = args.files or ["-"]
    all_findings: list[Finding] = []

    for target in targets:
        if target == "-":
            content = sys.stdin.read()
            label = "<stdin>"
        else:
            p = Path(target)
            if not p.is_file():
                print(f"error: file not found: {target}", file=sys.stderr)
                return 2
            content = p.read_text(encoding="utf-8")
            label = str(p)
        all_findings.extend(
            check_text(content, path=label, lang=args.lang, max_sentence_words=args.max_words)
        )

    for finding in all_findings:
        print(finding.format())

    errors = sum(1 for f in all_findings if f.severity == "ERROR")
    warns = sum(1 for f in all_findings if f.severity == "WARN")
    print(f"summary: {errors} ERROR, {warns} WARN")

    if errors > 0 or (args.strict and warns > 0):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
