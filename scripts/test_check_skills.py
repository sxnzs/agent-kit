#!/usr/bin/env python3
"""Unit tests for scripts/check_skills.py."""

from __future__ import annotations

import io
import sys
import tempfile
import unittest
from contextlib import redirect_stderr
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_skills import main, validate_skills  # noqa: E402


def _update_bucket_readme(root: Path, bucket: str, name: str, *, user_invoked: bool) -> None:
    readme = root / bucket / "README.md"
    if not readme.is_file():
        readme.write_text(
            f"# {bucket}\n\n## User-invoked\n\n## Model-invoked\n",
            encoding="utf-8",
        )
    text = readme.read_text(encoding="utf-8")
    entry = f"* [{name}]({name}/SKILL.md): summary.\n"
    if entry in text:
        return
    marker = "## User-invoked\n" if user_invoked else "## Model-invoked\n"
    text = text.replace(marker, marker + "\n" + entry, 1)
    readme.write_text(text, encoding="utf-8")


def _write_valid_skill(
    root: Path,
    name: str = "demo-skill",
    bucket: str = "engineering",
    *,
    user_invoked: bool = False,
    list_in_readme: bool = True,
) -> Path:
    skill = root / bucket / name
    (skill / "references").mkdir(parents=True)
    (skill / "agents").mkdir(parents=True)
    if user_invoked:
        fm = f"---\nname: {name}\ndescription: Run the demo workflow.\ndisable-model-invocation: true\n---\n\n"
        twin = (
            f"interface:\n  display_name: {name}\n  short_description: Run the demo workflow.\n"
            "policy:\n  allow_implicit_invocation: false\n"
        )
    else:
        fm = f"---\nname: {name}\ndescription: Demo skill. Use when testing.\n---\n\n"
        twin = f"interface:\n  display_name: {name}\n  short_description: Demo skill.\n"
    (skill / "SKILL.md").write_text(
        f"{fm}# Demo\n\nSee [guide](references/guide.md).\n",
        encoding="utf-8",
    )
    (skill / "agents" / "openai.yaml").write_text(twin, encoding="utf-8")
    (skill / "references" / "guide.md").write_text("# Guide\n\nDetails.\n", encoding="utf-8")
    if list_in_readme:
        _update_bucket_readme(root, bucket, name, user_invoked=user_invoked)
    return skill


class CheckSkillsTests(unittest.TestCase):
    def test_valid_skill_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            skills_dir = Path(tmp) / "skills"
            _write_valid_skill(skills_dir)
            self.assertEqual(validate_skills(skills_dir, None), [])

    def test_missing_skills_dir_exits_cleanly(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            missing = Path(tmp) / "does-not-exist"
            buf = io.StringIO()
            with redirect_stderr(buf):
                rc = main(["--skills-dir", str(missing)])
            self.assertEqual(rc, 1)
            self.assertIn("skills directory not found", buf.getvalue())

    def test_frontmatter_and_length_limits(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            skills_dir = Path(tmp) / "skills"
            skill = _write_valid_skill(skills_dir, name="Bad_Slug")
            long_desc = "x" * 1025
            long_body = "\n".join(["line"] * 500)
            (skill / "SKILL.md").write_text(
                f"---\nname: Bad_Slug\ndescription: {long_desc}\nextra: 1\n---\n{long_body}\n",
                encoding="utf-8",
            )
            errors = validate_skills(skills_dir, None)
            self.assertEqual(len(errors), 6, errors)
            self.assertIn("invalid frontmatter keys", errors[0])
            self.assertIn("invalid skill slug", errors[1])
            self.assertIn("description exceeds 1024 chars", errors[2])
            self.assertIn("must include 'Use when'", errors[3])
            self.assertIn("limit < 500", errors[4])
            self.assertIn("unreachable markdown file", errors[5])

    def test_orphan_cycle_detected_by_reachability(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            skills_dir = Path(tmp) / "skills"
            skill = _write_valid_skill(skills_dir)
            (skill / "references" / "a.md").write_text("# A\nSee [b](b.md).\n", encoding="utf-8")
            (skill / "references" / "b.md").write_text("# B\nSee [a](a.md).\n", encoding="utf-8")
            errors = validate_skills(skills_dir, None)
            self.assertEqual(
                errors,
                [
                    f"{skill / 'references' / 'a.md'}: unreachable markdown file under references/",
                    f"{skill / 'references' / 'b.md'}: unreachable markdown file under references/",
                ],
            )

    def test_broken_link_detected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            skills_dir = Path(tmp) / "skills"
            skill = _write_valid_skill(skills_dir)
            (skill / "SKILL.md").write_text(
                "---\nname: demo-skill\ndescription: Demo. Use when testing.\n---\n\n"
                "See [missing](references/missing.md) and [guide](references/guide.md).\n",
                encoding="utf-8",
            )
            errors = validate_skills(skills_dir, None)
            self.assertEqual(
                errors,
                [f"{skill / 'SKILL.md'}:6: broken link -> references/missing.md"],
            )

    def test_stale_reference_frontmatter_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            skills_dir = Path(tmp) / "skills"
            skill = _write_valid_skill(skills_dir)
            (skill / "references" / "guide.md").write_text(
                "---\nname: old\ndescription: old\n---\n\n# Guide\n",
                encoding="utf-8",
            )
            errors = validate_skills(skills_dir, None)
            self.assertEqual(
                errors,
                [f"{skill / 'references' / 'guide.md'}: reference file should not carry skill YAML frontmatter"],
            )

    def test_ghost_skill_fenced_and_inline_code_skipped(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            skills_dir = Path(tmp) / "skills"
            skill = _write_valid_skill(skills_dir)
            (skill / "references" / "guide.md").write_text(
                "# Guide\n\n"
                "Run next step.\n"
                "Inline `use write-swift` is ignored.\n"
                "```\nuse write-swift\n```\n"
                "Prose use write-swift is flagged.\n",
                encoding="utf-8",
            )
            errors = validate_skills(skills_dir, None)
            self.assertEqual(
                errors,
                [f"{skill / 'references' / 'guide.md'}:8: stale standalone skill reference 'use write-swift'"],
            )

    def test_symlink_check_missing_mismatch_and_broken(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            skills_dir = Path(tmp) / "skills"
            links_dir = Path(tmp) / "links"
            links_dir.mkdir()
            other_dir = Path(tmp) / "other"
            other_dir.mkdir()
            _write_valid_skill(skills_dir, name="skill-a", bucket="engineering")
            _write_valid_skill(skills_dir, name="skill-b", bucket="productivity")
            _write_valid_skill(skills_dir, name="beta-skill", bucket="in-progress")
            (links_dir / "skill-a").symlink_to(other_dir)
            (links_dir / "dangling").symlink_to(Path(tmp) / "does-not-exist")
            errors = validate_skills(skills_dir, links_dir)
            self.assertEqual(
                errors,
                [
                    f"link mismatch: {links_dir / 'skill-a'} -> {other_dir.resolve()} (expected {(skills_dir / 'engineering' / 'skill-a').resolve()})",
                    f"missing link in {links_dir}: skill-b",
                    f"broken symlink in {links_dir}: {links_dir / 'dangling'}",
                ],
            )

    def test_duplicate_skill_name_across_buckets_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            skills_dir = Path(tmp) / "skills"
            _write_valid_skill(skills_dir, name="dup-skill", bucket="engineering")
            _write_valid_skill(skills_dir, name="dup-skill", bucket="productivity")
            errors = validate_skills(skills_dir, None)
            self.assertEqual(len(errors), 1, errors)
            self.assertIn("duplicate skill name 'dup-skill'", errors[0])

    def test_valid_user_invoked_and_quoted_colon(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            skills_dir = Path(tmp) / "skills"
            _write_valid_skill(skills_dir, name="u-skill", user_invoked=True)
            skill = _write_valid_skill(skills_dir, name="m-skill")
            (skill / "SKILL.md").write_text(
                '---\nname: m-skill\ndescription: "Demo: details. Use when testing."\nargument-hint: "[path]"\n---\n\n'
                "# Demo\n\nSee [guide](references/guide.md).\n",
                encoding="utf-8",
            )
            self.assertEqual(validate_skills(skills_dir, None), [])

    def test_unquoted_colon_and_indicator_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            skills_dir = Path(tmp) / "skills"
            skill = _write_valid_skill(skills_dir, name="bad-quote")
            (skill / "SKILL.md").write_text(
                "---\nname: bad-quote\ndescription: Demo: details. Use when testing.\nargument-hint: [path]\n---\n\n"
                "# Demo\n\nSee [guide](references/guide.md).\n",
                encoding="utf-8",
            )
            errors = validate_skills(skills_dir, None)
            self.assertEqual(len(errors), 2, errors)
            self.assertIn("frontmatter 'description' must be quoted", errors[0])
            self.assertIn("frontmatter 'argument-hint' must be quoted", errors[1])

    def test_user_invoked_description_rules(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            skills_dir = Path(tmp) / "skills"
            skill = _write_valid_skill(skills_dir, name="bad-user", user_invoked=True)
            long_two = ("A" * 150) + ". Use when doing stuff."
            (skill / "SKILL.md").write_text(
                f"---\nname: bad-user\ndescription: {long_two}\ndisable-model-invocation: true\n---\n\n"
                "# Demo\n\nSee [guide](references/guide.md).\n",
                encoding="utf-8",
            )
            errors = validate_skills(skills_dir, None)
            self.assertEqual(len(errors), 3, errors)
            self.assertIn("exceeds 160 chars", errors[0])
            self.assertIn("must not contain 'Use when'", errors[1])
            self.assertIn("must be one sentence", errors[2])

    def test_mismatched_codex_twin_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            skills_dir = Path(tmp) / "skills"
            u_skill = _write_valid_skill(skills_dir, name="u-mismatch", user_invoked=True)
            (u_skill / "agents" / "openai.yaml").write_text(
                "interface:\n  display_name: U\n  short_description: Short.\n",
                encoding="utf-8",
            )
            m_skill = _write_valid_skill(skills_dir, name="m-mismatch", user_invoked=False)
            (m_skill / "agents" / "openai.yaml").write_text(
                "interface:\n  display_name: M\n  short_description: Short.\n"
                "policy:\n  allow_implicit_invocation: false\n",
                encoding="utf-8",
            )
            errors = validate_skills(skills_dir, None)
            self.assertEqual(len(errors), 2, errors)
            self.assertIn("model-invoked skill must not set policy.allow_implicit_invocation: false", errors[0])
            self.assertIn("user-invoked skill must set policy.allow_implicit_invocation: false", errors[1])

    def test_cross_skill_links_and_calls_validated(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            skills_dir = Path(tmp) / "skills"
            _write_valid_skill(skills_dir, name="model-target", user_invoked=False)
            _write_valid_skill(skills_dir, name="user-target", user_invoked=True)
            caller = _write_valid_skill(skills_dir, name="caller-skill", user_invoked=False)
            (caller / "SKILL.md").write_text(
                "---\nname: caller-skill\ndescription: Caller. Use when testing.\n---\n\n"
                "# Caller\n\n"
                "See [guide](references/guide.md).\n"
                'Call the Skill tool with "model-target".\n'
                "Otherwise tell the user to run the user-target skill.\n",
                encoding="utf-8",
            )
            self.assertEqual(validate_skills(skills_dir, None), [])

            (caller / "SKILL.md").write_text(
                "---\nname: caller-skill\ndescription: Caller. Use when testing.\n---\n\n"
                "# Caller\n\n"
                "See [guide](references/guide.md) and [leak](../model-target/SKILL.md).\n"
                "Do not read `model-target/references/guide.md` or `~/.agents/skills/model-target/SKILL.md`.\n"
                'Call the Skill tool with "user-target".\n'
                'Call the Skill tool with "ghost-skill".\n'
                "Otherwise tell the user to run the missing-cmd skill.\n"
                "Or tell the user to run /user-target.\n"
                "Then suggest **model-target** or run **ghost-skill**.\n"
                "Start with **one** change and run **fast** checks.\n",
                encoding="utf-8",
            )
            errors = validate_skills(skills_dir, None)
            self.assertEqual(len(errors), 8, errors)
            self.assertIn("link leaves skill folder", errors[0])
            self.assertIn("backticked path points into another skill 'model-target'", errors[1])
            self.assertIn("backticked path points into another skill 'model-target'", errors[2])
            self.assertIn("Skill tool call targets user-invoked skill 'user-target'", errors[3])
            self.assertIn("Skill tool call targets unknown skill 'ghost-skill'", errors[4])
            self.assertIn("'tell the user to run the missing-cmd skill' names unknown skill", errors[5])
            self.assertIn("use host-neutral 'tell the user to run the user-target skill'", errors[6])
            self.assertIn("bold skill mention names unknown skill 'ghost-skill'", errors[7])

    def test_bucket_readme_and_ask_kit_listing_enforced(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            skills_dir = Path(tmp) / "skills"
            _write_valid_skill(skills_dir, name="listed-user", bucket="engineering", user_invoked=True)
            _write_valid_skill(skills_dir, name="unlisted-skill", bucket="engineering", user_invoked=False, list_in_readme=False)
            ask_kit = _write_valid_skill(skills_dir, name="ask-kit", bucket="productivity", user_invoked=True)
            (ask_kit / "SKILL.md").write_text(
                "---\nname: ask-kit\ndescription: Route to skills.\ndisable-model-invocation: true\n---\n\n"
                "# Ask Kit\n\nSee [guide](references/guide.md).\n- `unlisted-skill`: model skill.\n",
                encoding="utf-8",
            )
            errors = validate_skills(skills_dir, None)
            self.assertEqual(len(errors), 2, errors)
            self.assertIn("skill 'unlisted-skill' missing under 'Model-invoked'", errors[0])
            self.assertIn("user-invoked skill '`listed-user`' not listed in ask-kit", errors[1])


if __name__ == "__main__":
    unittest.main()
