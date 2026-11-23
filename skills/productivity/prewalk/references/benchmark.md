# DeepSeek 4.1 Flash 1017 quality benchmark prompts

Run these before and after prewalk to verify real improvement:

1. **Spanish explainer**: Draft a 250-word Latin American Spanish explanation of why an LLM needs a harness to run shell commands. Gate: `check_prose.py --lang es --strict` exits 0; zero English calques, zero em-dashes, active verbs.
2. **Human-facing technical reply**: Write a 120-word explanation to a developer explaining why a flaky integration test failed due to shared temp paths and how to fix it. Gate: `check_prose.py --strict` exits 0; no throat-clearing, no `not X, but Y` templates.
3. **Code extension**: Given one landed Rust module + unit test following workspace lints, add a second sibling module matching the exact error type, visibility, and test style. Gate: repo test + clippy pass with 0 warnings and 0 inline `allow`.
