# Jev search: provider, social, and schema details

Read when debugging retrieval or judge fallbacks, interpreting `--json` fields, or querying social sources (`reddit`, `x`).

## Retrieval and judge backends

- **Retrieval, primary**: Exa keyless MCP search (`https://mcp.exa.ai/mcp`, tool `web_search_exa`). No key. Keep the `User-Agent` header; the endpoint rejects clients without one. Its free IP quota bursts hard (about 40 searches) and blocks for hours. Concurrent requests per IP are serialized by Exa, so multi-source lanes run sequentially on purpose.
- **Retrieval, fallback**: Brave web search API (`BRAVE_API_KEY`, `X-Subscription-Token` header). Free tier is 1 request/sec; `JEV_SEARCH_ENGINE` sets the default engine. The payload names the serving engine under `retrieval`, and human output prints `engine: brave` when fallback fires.
- **Judgment, free default**: `jev-1.13-free` via local OpenCode (`POST /api/experimental/generate/decisions`), using stored Console auth (`cost: 0`, `billing_source: "free"`). Note: Jev is a Console model (`jev-1.13` paid, `jev-1.13-free` limited-time free) served from `https://opencode.ai/inference/systemone/v1/systemone`, not part of the Go plan.
- **Judgment, paid fallbacks** (auto-detected in order): TypeSafe direct (`TYPESAFE_API_KEY`, `model: "jev-latest"`), OpenRouter (`OPENROUTER_API_KEY`, `~typesafe/jev-latest`), Cloudflare (`CLOUDFLARE_ACCOUNT_ID` plus `CLOUDFLARE_API_TOKEN` or `JEV_CLOUDFLARE_API_TOKEN`), Vercel AI Gateway (`AI_GATEWAY_API_KEY`). `JEV_PROVIDER` or `--judge` forces one; `JEV_MODEL` pins the model on gateway providers.
- **Validation and retries**: every answer is validated for exact question ids, values in `[0, 1]`, and non-negative integer usage counters. Retries cover `408`, `409`, `429`, and `5xx`, honor `Retry-After` (seconds or HTTP date), and use jittered exponential backoff capped at 5s.
- **Caching**: payloads cache under `~/.cache/jev-search/` (override with `JEV_SEARCH_CACHE_DIR`) for 6 hours, keyed by query, sources, and judge, capped at 200 entries (FIFO). Repeats print `cache: hit`.
- **Observed cost and latency (2026-11-21)**: about 3k input tokens for 12 candidates in one request; paid estimate is `$0.042` per million input tokens (roughly `$0.00013` per search); single-source median about 630ms, cache hit about 50ms. Free model is `jev-1.13`; paid is `jev-1.14`.

## Social sources

- `web`: default, no filter.
- `reddit`: appends `site:reddit.com`. Threads index with post text and scores; Reddit blocks direct page fetches, so the Exa highlight is the deepest access available.
- `x`: appends `site:x.com`, but Exa cannot index X behind its login wall. Results arrive via mirrors and thread readers (such as threadnavigator, unrollnow, bittide) plus occasional aggregator blogs. Near-duplicate titles across mirrors drop at `0.75` token overlap. Official Search1API Ask API is the cleanest X source observed so far.

## JSON output schema

Top-level fields:

- `query`, `sources`, `retrieval`, `threshold`, `candidates`, `dropped`
- `judge`: `backend`, `model`, `usage` (`input_tokens`, `output_tokens`), `cost_usd`, optional `fallbacks` or `error`
- `best_choice`, `best_confidence`, optional `all_below_threshold` and `cache`
- `results[]`: `title`, `url`, `snippet`, `published`, `relevance`, `best_pick`, `retrieval_rank`, `source`, optional `weak`

Human output prints `[score] title` with `weak` and `*` on the best pick, URL, then a short snippet.
