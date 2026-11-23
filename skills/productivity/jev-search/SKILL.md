---
name: jev-search
description: "Search the web where result relevance matters, ranked by TypeSafe Jev. Use when the user says jev search or search with jev, or when a plain lookup is not enough: source picking, dedupe, relevance scores, or filtering out off-topic hits. Not for code-base search or for logged-in pages."
---

# Jev search

Retrieve web candidates, then run one batched Jev request that scores every candidate for relevance and picks the single best source. Results below `0.5` are dropped (keeping the top two flagged `weak` if everything scores low), near-duplicate titles are merged, and results sort by best pick then relevance.

For provider transport fallbacks, retry policy, social-source quirks, latency/cost notes, and the full JSON schema, read [details.md](references/details.md).

## When to use which search

- Built-in `websearch`: fastest, one call, no scoring. Use for a quick fact.
- Jev search: deduped, scored, and best-picked in one call. Use when citing or comparing sources, or when a query is broad and noisy.
- If `SEARCH1API_API_KEY` is set, prefer the official Search1API Ask API (`POST https://api.search1api.com/ask`) for multi-engine routing and intent/time-window detection.

## Run it

```sh
uv run --script ~/.agents/skills/jev-search/jev_search.py "query" --max-results 8
```

Core flags:

- `--engine auto|exa|brave`: `auto` (default) tries keyless Exa first and falls back to Brave (`BRAVE_API_KEY`) when Exa fails or hits its burst quota.
- `--judge auto|opencode|typesafe|openrouter|cloudflare|vercel|none`: `auto` (default) tries free `jev-1.13-free` via local OpenCode, then configured paid providers; `none` skips scoring.
- `--sources web,reddit,x`: comma list (default `web`). Lanes run sequentially and merge round robin with title dedupe.
- `--no-cache`: bypass the 6-hour cache under `~/.cache/jev-search/`.
- `--json`: structured JSON output.

## Read the scores correctly

- A score is Jev's calibrated probability that the result helps with the request, not proof that the claim is true. Snippets can be stale.
- `best_pick` comes from a separate Choice judgment in the same call. When `best_pick` and top relevance disagree, read both results before citing either.
- A narrow band around `0.6` to `0.7` across every candidate usually means the query is ambiguous; rewrite the query rather than lowering the threshold.
- When every candidate lands below `0.5`, the top two return with `weak` and `all_below_threshold: true`.
- CJK ranking is weaker than English; spot-check kept results on Chinese queries.

## Failure fallbacks

- Exa keyless rate limits hard under bursts and fails fast with a reset time. With `BRAVE_API_KEY` set, `--engine auto` falls back to Brave; without it, fall back to built-in `websearch` and say so.
- The free OpenCode route requires the local OpenCode service running with the `opencode` provider connected. Outside OpenCode, set `OPENCODE_API_KEY` or a paid provider key so `auto` can judge; otherwise results print unscored with `judge.error`.
- Do not retry `401` or `402` from any judge (key or billing problem). The script retries `408`, `409`, `429`, and `5xx` automatically.
- The script does not detect intent or time windows; add those terms to the query or filter results yourself.
