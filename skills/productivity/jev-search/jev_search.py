# /// script
# requires-python = ">=3.11"
# dependencies = ["httpx>=0.27"]
# ///
"""Jev as a search engine: retrieve with Exa, judge relevance with Jev.

Mirrors Search1API's Ask pipeline without a Search1API key: keyless Exa MCP
retrieval, then one batched decision request that scores every candidate
against the request. Results below the relevance threshold are dropped,
duplicates merged, and the rest ordered by Jev's probability.

The judge runs free by default through the local OpenCode service
(`jev-1.13-free` on the Console endpoint, cost 0). It falls back to TypeSafe
directly with `jev-latest` when `TYPESAFE_API_KEY` is set.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import random
import re
import shutil
import subprocess
import sys
import time
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any

import httpx

EXA_MCP_URL = "https://mcp.exa.ai/mcp"
BRAVE_URL = "https://api.search.brave.com/res/v1/web/search"
TYPESAFE_URL = "https://api.typesafe.ai/v1/systemone"
TYPESAFE_BASE_URL = "https://api.typesafe.ai"
OPENROUTER_URL = "https://openrouter.ai/api/alpha/decisions"
CLOUDFLARE_URL = "https://api.cloudflare.com/client/v4/accounts/{account}/ai/run"
VERCEL_URL = "https://ai-gateway.vercel.sh/v4/ai/evaluation-model"
OPENCODE_DECISIONS = "/api/experimental/generate/decisions"
OPENCODE_MODEL = {"providerID": "opencode", "id": "jev-1.13-free"}
USER_AGENT = "jev-search/0.1"
OPENROUTER_TITLE = "jev-search"
OPENROUTER_REFERER = "https://github.com/sxnzs/agent-kit"
MIN_RELEVANCE = 0.5
MAX_CANDIDATES = 20
PRICE_PER_MTOK_IN = 0.042
RETRYABLE_STATUSES = {408, 409, 429}
MAX_ATTEMPTS = 3
MAX_DELAY_S = 5.0
BLOCK_RE = re.compile(r"^Title: ", re.MULTILINE)
JUDGE_PROMPT = (
    "Judge whether `results[{i}]` is relevant to the search request `request`. "
    "Relevant means its title or snippet would plausibly help answer or inform "
    "the request, weighing `published` when the request implies recency. "
    "Off topic, unrelated, or stale-looking results are not relevant."
)
BEST_PROMPT = (
    "Which single result is the best direct answer to the search request "
    "`request`? Pick the one result a careful reader would open first."
)
CRITERIA = {
    "true": "On topic and likely useful for the request",
    "false": "Off topic, unrelated, or not useful for the request",
}
SOURCE_FILTERS = {
    "reddit": "site:reddit.com",
    "x": "site:x.com",
    "twitter": "site:twitter.com",
}


def _mcp_call(
    client: httpx.Client, body: dict[str, Any], headers: dict[str, str]
) -> dict[str, Any]:
    """Send one JSON-RPC request to the Exa MCP endpoint and return its result."""
    for attempt in range(3):
        resp = client.post(EXA_MCP_URL, json=body, headers=headers)
        if resp.status_code == 429:
            wait = float(resp.headers.get("retry-after", 3 * (attempt + 1)))
            if wait > 60:
                reset = time.strftime("%H:%M", time.localtime(time.time() + wait))
                raise RuntimeError(
                    f"Exa free quota exhausted; retry-after {int(wait)}s "
                    f"(resets about {reset}). Rerun later, use a cached query, "
                    "or get a free Exa account for a personal allowance"
                )
            time.sleep(min(wait, 15))
            continue
        resp.raise_for_status()
        text = resp.text
        payloads = [line[6:] for line in text.splitlines() if line.startswith("data: ")]
        raw = payloads[0] if payloads else text
        return json.loads(raw)
    raise RuntimeError("Exa MCP rate limited after 3 attempts")


def _parse_blocks(text: str) -> list[dict[str, str]]:
    """Split Exa's `Title:/URL:/Highlights:` text into result records."""
    chunks = [c for c in BLOCK_RE.split(text) if c.strip()]
    rows: list[dict[str, str]] = []
    for chunk in chunks:
        title = chunk.splitlines()[0].strip() if chunk.splitlines() else ""
        url_match = re.search(r"^URL:\s*(\S+)", chunk, re.MULTILINE)
        published = re.search(r"^Published:\s*(.+)$", chunk, re.MULTILINE)
        body = re.split(
            r"^(?:Highlights|Text):\s*$", chunk, maxsplit=1, flags=re.MULTILINE
        )
        snippet = re.sub(r"\s+", " ", body[1]).strip()[:400] if len(body) > 1 else ""
        if title and url_match:
            rows.append(
                {
                    "title": title,
                    "url": url_match.group(1),
                    "snippet": snippet,
                    "published": published.group(1).strip() if published else "N/A",
                }
            )
    return rows


def retrieve(
    query: str,
    limit: int,
    source: str = "web",
    client: httpx.Client | None = None,
) -> list[dict[str, str]]:
    """Fetch candidates from Exa's keyless MCP search tool, optionally source scoped.

    The MCP initialize handshake is skipped: this endpoint answers tools/call
    without it, and the handshake only adds a round trip.
    """
    scoped = f"{query} {SOURCE_FILTERS[source]}" if source in SOURCE_FILTERS else query
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/json, text/event-stream",
    }
    owned = client is None
    if owned:
        client = httpx.Client(timeout=30.0)
    try:
        result = _mcp_call(
            client,
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": "web_search_exa",
                    "arguments": {"query": scoped, "numResults": limit},
                },
            },
            headers,
        )
    finally:
        if owned:
            client.close()
    if "error" in result:
        raise RuntimeError(f"Exa MCP error: {result['error']}")
    content = (result.get("result") or {}).get("content") or []
    text = "".join(
        part.get("text", "") for part in content if part.get("type") == "text"
    )
    seen: set[str] = set()
    unique: list[dict[str, str]] = []
    for row in _parse_blocks(text):
        key = row["url"].split("#")[0].rstrip("/").lower()
        if key in seen:
            continue
        seen.add(key)
        unique.append(row)
    return unique[:MAX_CANDIDATES]


def retrieve_brave(
    query: str,
    limit: int,
    source: str = "web",
    client: httpx.Client | None = None,
) -> list[dict[str, str]]:
    """Fetch candidates from Brave's web search API using BRAVE_API_KEY."""
    key = os.environ.get("BRAVE_API_KEY")
    if not key:
        raise RuntimeError("BRAVE_API_KEY is not set")
    scoped = f"{query} {SOURCE_FILTERS[source]}" if source in SOURCE_FILTERS else query
    headers = {"X-Subscription-Token": key, "Accept": "application/json"}
    owned = client is None
    if owned:
        client = httpx.Client(timeout=30.0)
    try:
        payload = _request_json(
            client,
            BRAVE_URL,
            None,
            headers,
            {"q": scoped, "count": min(limit, 20)},
        )
    finally:
        if owned:
            client.close()
    results = (payload.get("web") or {}).get("results") or []
    seen: set[str] = set()
    unique: list[dict[str, str]] = []
    for row in results:
        url = row.get("url") or ""
        title = re.sub(r"\s+", " ", row.get("title") or "").strip()
        if not url or not title or url.split("#")[0].rstrip("/").lower() in seen:
            continue
        seen.add(url.split("#")[0].rstrip("/").lower())
        unique.append(
            {
                "title": title,
                "url": url,
                "snippet": re.sub(r"<[^>]+>", "", row.get("description") or "")[:400],
                "published": row.get("age") or row.get("date") or "N/A",
            }
        )
    return unique[:MAX_CANDIDATES]


def _state(query: str, results: list[dict[str, str]]) -> dict[str, Any]:
    return {
        "request": query,
        "results": [
            {
                "title": r["title"],
                "url": r["url"],
                "snippet": r["snippet"][:240],
                "published": r.get("published") or "N/A",
                "source": r.get("source") or "web",
            }
            for r in results
        ],
    }


def _retry_after_seconds(header: str | None) -> float | None:
    """Parse Retry-After as delay seconds or an HTTP date."""
    if not header:
        return None
    value = header.strip()
    try:
        return max(0.0, float(value))
    except ValueError:
        pass
    try:
        target = parsedate_to_datetime(value)
    except (TypeError, ValueError):
        return None
    return max(0.0, target.timestamp() - time.time())


def _backoff_seconds(header: str | None, attempt: int) -> float:
    """Honor Retry-After, else jittered exponential backoff, capped."""
    parsed = _retry_after_seconds(header)
    delay = parsed if parsed is not None else 0.25 * 2 ** (attempt - 1)
    delay += random.uniform(0.0, 0.1)
    return min(delay, MAX_DELAY_S)


def _request_json(
    client: httpx.Client,
    url: str,
    body: dict[str, Any] | None,
    headers: dict[str, str],
    params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """POST, or GET when body is None, with the shared retry policy."""
    for attempt in range(1, MAX_ATTEMPTS + 1):
        if body is None:
            resp = client.get(url, headers=headers, params=params)
        else:
            resp = client.post(url, headers=headers, json=body)
        retryable = resp.status_code in RETRYABLE_STATUSES or resp.status_code >= 500
        if retryable and attempt < MAX_ATTEMPTS:
            time.sleep(_backoff_seconds(resp.headers.get("retry-after"), attempt))
            continue
        resp.raise_for_status()
        payload = resp.json()
        if not isinstance(payload, dict):
            raise TypeError("response envelope is not an object")
        return payload
    raise RuntimeError("retry budget exhausted")


ROUNDING_STEP = 0.005
MAX_SUM_DRIFT = 0.05


def _distribution(value: Any, keys: list[str]) -> dict[str, float]:
    """Check a choice distribution: exact keys, finite probabilities, sum near 1."""
    if not isinstance(value, dict) or set(value) != set(keys):
        raise RuntimeError("distribution must contain exactly the criteria keys")
    entries: dict[str, float] = {}
    for key in keys:
        probability = value[key]
        if (
            not isinstance(probability, (int, float))
            or isinstance(probability, bool)
            or not math.isfinite(probability)
            or not 0.0 <= probability <= 1.0
        ):
            raise RuntimeError(
                "distribution must contain finite probabilities in [0,1]"
            )
        entries[key] = float(probability)
    nonzero = sum(1 for probability in entries.values() if probability > 0)
    tolerance = min(MAX_SUM_DRIFT, max(0.01, ROUNDING_STEP * nonzero)) + 1e-9
    if abs(sum(entries.values()) - 1.0) > tolerance:
        raise RuntimeError("distribution must sum to approximately 1")
    return entries


def _validate_answers(
    questions: dict[str, dict[str, Any]], answers: Any
) -> dict[str, dict[str, Any]]:
    """Reject malformed or misaligned Jev answers before they steer a result."""
    if not isinstance(answers, dict):
        raise TypeError("answers must be an object")
    if set(answers) != set(questions):
        raise RuntimeError("answer ids do not match the questions")
    validated: dict[str, dict[str, Any]] = {}
    for qid, question in questions.items():
        answer = answers[qid]
        if not isinstance(answer, dict) or answer.get("type") != question["type"]:
            raise RuntimeError(f"{qid}: missing answer or wrong type")
        if question["type"] == "noul":
            value = answer.get("noul")
            if (
                not isinstance(value, (int, float))
                or isinstance(value, bool)
                or not math.isfinite(value)
                or not 0.0 <= value <= 1.0
            ):
                raise RuntimeError(f"{qid}: noul must be finite in [0,1]")
            validated[qid] = {"type": "noul", "noul": float(value)}
            continue
        if question["type"] == "choice":
            keys = list(question["criteria"])
            probabilities = _distribution(answer.get("probabilities"), keys)
            choice = answer.get("choice")
            if not isinstance(choice, str) or choice not in question["criteria"]:
                raise RuntimeError(f"{qid}: choice is outside criteria")
            if max(probabilities.values()) - probabilities[choice] > 0.01 + 1e-9:
                raise RuntimeError(f"{qid}: choice is not a distribution maximum")
            confidence = answer.get("confidence")
            if confidence is not None and (
                isinstance(confidence, bool)
                or not isinstance(confidence, (int, float))
                or not math.isfinite(confidence)
            ):
                raise RuntimeError(f"{qid}: confidence must be finite or null")
            validated[qid] = {
                "type": "choice",
                "choice": choice,
                "probabilities": probabilities,
                "confidence": None if confidence is None else float(confidence),
            }
            continue
        raise RuntimeError(f"{qid}: unsupported question type")
    return validated


def _usage(usage: Any) -> dict[str, int]:
    """Normalize provider usage to non-negative input/output token counters."""
    if usage is None:
        return {"input_tokens": 0, "output_tokens": 0}
    if not isinstance(usage, dict):
        raise TypeError("invalid usage")
    tokens = {
        "input_tokens": usage.get(
            "input_tokens", usage.get("inputTokens", usage.get("input", 0))
        ),
        "output_tokens": usage.get(
            "output_tokens", usage.get("outputTokens", usage.get("output", 0))
        ),
    }
    for value in tokens.values():
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            raise RuntimeError("usage counters must be non-negative integers")
    return tokens


def _meta(name: str, model: Any, usage: Any) -> dict[str, Any]:
    """Build judge metadata with the Jev input-token cost estimate."""
    tokens = _usage(usage)
    effective = model if isinstance(model, str) and model.strip() else name
    return {
        "backend": name,
        "model": effective,
        "usage": tokens,
        "cost_usd": round(tokens["input_tokens"] / 1_000_000 * PRICE_PER_MTOK_IN, 6),
    }


def _questions(results: list[dict[str, str]]) -> dict[str, dict[str, Any]]:
    """Fan out: one relevance noul per candidate plus one best-source choice.

    Independent judgments in a single request, the same pattern jev-browser
    uses per step. The choice cannot see the nouls, which keeps the best-source
    pick an honest cross-check on the relevance scores.
    """
    questions: dict[str, dict[str, Any]] = {
        f"r{i}": {
            "type": "noul",
            "instructions": JUDGE_PROMPT.format(i=i),
            "criteria": {
                "true": {"what": CRITERIA["true"]},
                "false": {"what": CRITERIA["false"]},
            },
        }
        for i in range(len(results))
    }
    questions["best"] = {
        "type": "choice",
        "instructions": BEST_PROMPT,
        "criteria": {f"r{i}": r["title"][:80] for i, r in enumerate(results)},
    }
    return questions


def _scores(answers: dict[str, dict[str, Any]], n: int) -> list[float]:
    return [float(answers[f"r{i}"]["noul"]) for i in range(n)]


def _best(answers: dict[str, dict[str, Any]]) -> dict[str, Any]:
    return answers["best"]


def _judgments(answers: dict[str, dict[str, Any]], n: int) -> dict[str, Any]:
    return {"relevance": _scores(answers, n), "best": _best(answers)}


def judge_opencode(
    query: str, results: list[dict[str, str]]
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Ask the local OpenCode service for free Jev decisions."""
    if shutil.which("opencode") is None:
        raise RuntimeError("opencode CLI not on PATH")
    payload = {
        "model": OPENCODE_MODEL,
        "input": [{"type": "json", "value": _state(query, results)}],
        "questions": [
            {
                "type": "predicate",
                "name": f"r{i}",
                "instructions": JUDGE_PROMPT.format(i=i),
                "criteria": CRITERIA,
            }
            for i in range(len(results))
        ]
        + [
            {
                "type": "choice",
                "name": "best",
                "instructions": BEST_PROMPT,
                "choices": [
                    {"value": f"r{i}", "label": r["title"][:80]}
                    for i, r in enumerate(results)
                ],
            }
        ],
    }
    proc = subprocess.run(
        ["opencode", "api", "post", OPENCODE_DECISIONS, "--data", json.dumps(payload)],
        capture_output=True,
        text=True,
        timeout=90,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(
            proc.stderr.strip()[:200] or f"opencode api exit {proc.returncode}"
        )
    body = json.loads(proc.stdout)
    data = body.get("data") or {}
    answers: dict[str, dict[str, Any]] = {}
    for answer in data.get("answers") or []:
        if not isinstance(answer, dict) or not answer.get("name"):
            continue
        if answer["type"] == "predicate":
            answers[answer["name"]] = {
                "type": "noul",
                "noul": answer.get("probability"),
            }
        elif answer["type"] == "choice":
            answers[answer["name"]] = {
                "type": "choice",
                "choice": answer.get("choice"),
                "probabilities": {
                    p.get("value"): p.get("probability")
                    for p in answer.get("probabilities") or []
                    if isinstance(p, dict)
                },
                "confidence": answer.get("confidence"),
            }
    validated = _validate_answers(_questions(results), answers)
    native = (data.get("native") or {}).get("opencode") or {}
    meta = _meta(
        "opencode-free",
        native.get("model", OPENCODE_MODEL["id"]),
        data.get("tokens"),
    )
    meta["cost_usd"] = 0
    return _judgments(validated, len(results)), meta


def judge_typesafe(
    query: str, results: list[dict[str, str]]
) -> tuple[list[float], dict[str, Any]]:
    """Ask TypeSafe System One directly, using TYPESAFE_API_KEY."""
    key = os.environ.get("TYPESAFE_API_KEY")
    if not key:
        raise RuntimeError("TYPESAFE_API_KEY is not set")
    questions = _questions(results)
    body = {
        "model": "jev-latest",
        "state": _state(query, results),
        "questions": questions,
    }
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    with httpx.Client(timeout=25.0) as client:
        payload = _request_json(client, TYPESAFE_URL, body, headers)
    answers = _validate_answers(questions, payload.get("answers"))
    return _judgments(answers, len(results)), _meta(
        "typesafe", payload.get("model"), payload.get("usage")
    )


def _openrouter_model(model: str) -> str:
    if model in ("jev-latest", "typesafe/jev-latest", "~typesafe/jev-latest"):
        return "~typesafe/jev-latest"
    return model if model.startswith("typesafe/") else f"typesafe/{model}"


def judge_openrouter(
    query: str, results: list[dict[str, str]]
) -> tuple[list[float], dict[str, Any]]:
    """Ask Jev through OpenRouter's decisions endpoint."""
    key = os.environ.get("OPENROUTER_API_KEY", "")
    if not key.startswith("sk-or-"):
        raise RuntimeError("OPENROUTER_API_KEY is not set or not an sk-or- key")
    questions = _questions(results)
    slug = _openrouter_model(os.environ.get("JEV_MODEL", "jev-latest"))
    body = {"model": slug, "state": _state(query, results), "questions": questions}
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "HTTP-Referer": OPENROUTER_REFERER,
        "X-Title": OPENROUTER_TITLE,
        "X-OpenRouter-Title": OPENROUTER_TITLE,
    }
    with httpx.Client(timeout=25.0) as client:
        payload = _request_json(client, OPENROUTER_URL, body, headers)
    answers = _validate_answers(questions, payload.get("answers"))
    return _judgments(answers, len(results)), _meta(
        "openrouter", payload.get("model") or slug, payload.get("usage")
    )


def judge_cloudflare(
    query: str, results: list[dict[str, str]]
) -> tuple[list[float], dict[str, Any]]:
    """Ask Jev through Cloudflare's AI run endpoint."""
    token = os.environ.get("JEV_CLOUDFLARE_API_TOKEN") or os.environ.get(
        "CLOUDFLARE_API_TOKEN"
    )
    account = os.environ.get("CLOUDFLARE_ACCOUNT_ID")
    if not token or not account:
        raise RuntimeError("Cloudflare token and CLOUDFLARE_ACCOUNT_ID are required")
    questions = _questions(results)
    slug = os.environ.get("JEV_MODEL", "jev")
    slug = slug if slug.startswith("typesafe/") else f"typesafe/{slug}"
    body = {
        "model": slug,
        "input": {"state": _state(query, results), "questions": questions},
    }
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    with httpx.Client(timeout=25.0) as client:
        payload = _request_json(
            client, CLOUDFLARE_URL.format(account=account), body, headers
        )
    outer = payload.get("result")
    if isinstance(outer, dict) and outer.get("state") not in (None, "Completed"):
        raise RuntimeError("Cloudflare run did not complete")
    nested = outer.get("result") if isinstance(outer, dict) else None
    data = nested if isinstance(nested, dict) else outer or payload
    answers = _validate_answers(questions, data.get("answers"))
    return _judgments(answers, len(results)), _meta(
        "cloudflare", data.get("model") or slug, data.get("usage")
    )


def judge_vercel(
    query: str, results: list[dict[str, str]]
) -> tuple[list[float], dict[str, Any]]:
    """Ask Jev through the Vercel AI Gateway evaluation model endpoint."""
    key = os.environ.get("AI_GATEWAY_API_KEY")
    if not key:
        raise RuntimeError("AI_GATEWAY_API_KEY is not set")
    questions = _questions(results)
    adapted = {
        qid: (
            {
                "type": "boolean",
                "instructions": question["instructions"],
                "criteria": question["criteria"],
            }
            if question["type"] == "noul"
            else question
        )
        for qid, question in questions.items()
    }
    requested = os.environ.get("JEV_MODEL", "jev")
    effective = requested if requested.startswith("typesafe-ai/") else "typesafe-ai/jev"
    body = {"state": _state(query, results), "questions": adapted}
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "ai-gateway-protocol-version": "0.0.1",
        "ai-gateway-auth-method": "api-key",
        "ai-evaluation-model-specification-version": "4",
        "ai-model-id": effective,
    }
    with httpx.Client(timeout=25.0) as client:
        payload = _request_json(client, VERCEL_URL, body, headers)
    raw = payload.get("answers")
    if not isinstance(raw, dict):
        raise TypeError("answers must be an object")
    answers = {
        qid: (
            {"type": "noul", "noul": answer.get("probability")}
            if isinstance(answer, dict) and answer.get("type") == "boolean"
            else answer
        )
        for qid, answer in raw.items()
    }
    validated = _validate_answers(questions, answers)
    return _judgments(validated, len(results)), _meta(
        "vercel", payload.get("model") or effective, payload.get("usage")
    )


JUDGES = {
    "opencode": judge_opencode,
    "typesafe": judge_typesafe,
    "openrouter": judge_openrouter,
    "cloudflare": judge_cloudflare,
    "vercel": judge_vercel,
}
AUTO_ORDER = ["opencode", "typesafe", "openrouter", "cloudflare", "vercel"]


def _configured(name: str) -> bool:
    env = os.environ
    if name == "opencode":
        return shutil.which("opencode") is not None
    if name == "typesafe":
        return bool(env.get("TYPESAFE_API_KEY"))
    if name == "openrouter":
        return (env.get("OPENROUTER_API_KEY") or "").startswith("sk-or-")
    if name == "cloudflare":
        token = env.get("JEV_CLOUDFLARE_API_TOKEN") or env.get("CLOUDFLARE_API_TOKEN")
        return bool(token and env.get("CLOUDFLARE_ACCOUNT_ID"))
    if name == "vercel":
        return bool(env.get("AI_GATEWAY_API_KEY"))
    return False


def judge(
    query: str, results: list[dict[str, str]], backend: str
) -> tuple[list[float], dict[str, Any]]:
    """Run the requested judge, or the auto chain of configured providers."""
    if backend == "auto":
        names = [name for name in AUTO_ORDER if _configured(name)]
        if not names:
            raise RuntimeError(
                "no Jev provider configured: set TYPESAFE_API_KEY, "
                "OPENROUTER_API_KEY, CLOUDFLARE_ACCOUNT_ID + "
                "CLOUDFLARE_API_TOKEN, or AI_GATEWAY_API_KEY"
            )
    else:
        names = [backend]
    errors: list[str] = []
    for name in names:
        try:
            scores, meta = JUDGES[name](query, results)
            if errors:
                meta["fallbacks"] = errors
            return scores, meta
        except (
            httpx.HTTPError,
            RuntimeError,
            json.JSONDecodeError,
            KeyError,
            ValueError,
            TypeError,
            OSError,
            subprocess.SubprocessError,
        ) as exc:
            errors.append(f"{name}: {exc}")
    raise RuntimeError("; ".join(errors))


CACHE_TTL_S = 6 * 3600
CACHE_MAX_ENTRIES = 200


def _cache_dir() -> Path:
    override = os.environ.get("JEV_SEARCH_CACHE_DIR")
    return Path(override or "~/.cache/jev-search").expanduser()


def _cache_path(
    query: str, sources: tuple[str, ...], backend: str, engine: str
) -> Path:
    key = hashlib.sha256(
        f"{query}|{','.join(sources)}|{backend}|{engine}".encode()
    ).hexdigest()
    return _cache_dir() / f"{key}.json"


def _cache_read(path: Path) -> dict[str, Any] | None:
    try:
        entry = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return None
    payload = entry.get("payload")
    if (
        not isinstance(payload, dict)
        or time.time() - entry.get("cached_at", 0) > CACHE_TTL_S
    ):
        return None
    return payload


def _cache_write(path: Path, payload: dict[str, Any]) -> None:
    directory = path.parent
    try:
        directory.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"cached_at": time.time(), "payload": payload}))
        entries = sorted(
            directory.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True
        )
        for stale in entries[CACHE_MAX_ENTRIES:]:
            stale.unlink()
    except OSError:
        pass


def _title_tokens(title: str) -> set[str]:
    return {t for t in re.findall(r"[a-z0-9]+", title.lower()) if len(t) > 2}


def _near_duplicate(tokens: set[str], kept: list[set[str]]) -> bool:
    """True when a title repeats an already kept one across a different URL.

    X mirrors and syndicated copies reuse a title with tiny edits; without this
    they crowd the top slots that ranking should fill with distinct sources.
    """
    return any(
        len(tokens & other) / max(1, len(tokens | other)) >= 0.75 for other in kept
    )


def search(
    query: str,
    *,
    max_results: int = 8,
    backend: str = "auto",
    sources: tuple[str, ...] = ("web",),
    use_cache: bool = True,
    engine: str = "auto",
) -> dict[str, Any]:
    """Retrieve, rank, filter and return a search payload."""
    cache_file = _cache_path(query, sources, backend, engine)
    if use_cache and backend != "none":
        cached = _cache_read(cache_file)
        if cached is not None:
            cached = {**cached, "cache": "hit"}
            cached["results"] = cached["results"][:max_results]
            return cached
    per_source = max(3, min(MAX_CANDIDATES, max_results + 4))
    engines = (
        [engine]
        if engine != "auto"
        else ["exa"] + (["brave"] if os.environ.get("BRAVE_API_KEY") else [])
    )
    retrieval_errors: list[str] = []
    retrieval: str | None = None
    with httpx.Client(timeout=30.0) as client:
        for name in engines:
            fetch = retrieve if name == "exa" else retrieve_brave
            try:
                lanes = [fetch(query, per_source, source, client) for source in sources]
                retrieval = name
                break
            except (httpx.HTTPError, RuntimeError) as exc:
                retrieval_errors.append(f"{name}: {exc}")
    if retrieval is None:
        raise RuntimeError(
            "; ".join(retrieval_errors) or "no retrieval engine available"
        )
    merged: list[dict[str, str]] = []
    seen: set[str] = set()
    kept_titles: list[set[str]] = []
    cursor = 0
    while len(merged) < MAX_CANDIDATES and any(cursor < len(lane) for lane in lanes):
        for source, lane in zip(sources, lanes, strict=True):
            if cursor >= len(lane):
                continue
            row = lane[cursor]
            key = row["url"].split("#")[0].rstrip("/").lower()
            tokens = _title_tokens(row["title"])
            if key in seen or _near_duplicate(tokens, kept_titles):
                continue
            seen.add(key)
            kept_titles.append(tokens)
            merged.append({**row, "source": source})
            if len(merged) >= MAX_CANDIDATES:
                break
        cursor += 1
    candidates = merged
    if not candidates:
        return {"query": query, "results": [], "note": "no results retrieved"}
    judgments: dict[str, Any] | None = None
    meta: dict[str, Any] = {}
    if backend != "none":
        if backend == "auto":
            try:
                judgments, meta = judge(query, candidates, backend)
            except RuntimeError as exc:
                meta = {"error": str(exc)}
                backend = "none"
        else:
            judgments, meta = judge(query, candidates, backend)
    judged = backend != "none"
    best = (judgments or {}).get("best") if judged else None
    relevance = (judgments or {}).get("relevance") if judged else None
    scored: list[dict[str, Any]] = []
    for position, row in enumerate(candidates):
        score = relevance[position] if relevance else None
        pick = None
        if best:
            pick = float(best["probabilities"].get(f"r{position}", 0.0))
        entry = {**row, "relevance": score, "retrieval_rank": position + 1}
        if pick is not None:
            entry["best_pick"] = pick
        if judged:
            entry["weak"] = score is not None and score < MIN_RELEVANCE
        scored.append(entry)
    all_below = False
    if judged:
        ranked = [r for r in scored if not r["weak"]]
        if not ranked:
            all_below = True
            ranked = sorted(scored, key=lambda r: -(r["relevance"] or 0.0))[:2]
        ranked.sort(
            key=lambda r: (
                -(r.get("best_pick") or 0.0),
                -(r["relevance"] or 0.0),
                r["retrieval_rank"],
            )
        )
    else:
        ranked = scored
        ranked.sort(key=lambda r: r["retrieval_rank"])
    payload = {
        "query": query,
        "sources": list(sources),
        "retrieval": "exa-mcp-keyless" if retrieval == "exa" else "brave-api",
        "judge": meta if judged else {"skipped": True, **meta},
        "threshold": MIN_RELEVANCE if judged else None,
        "candidates": len(candidates),
        "dropped": len(candidates) - len(ranked) if judged else 0,
        "results": ranked,
    }
    if all_below:
        payload["all_below_threshold"] = True
    if best:
        payload["best_choice"] = best["choice"]
        payload["best_confidence"] = best.get("confidence")
    if use_cache and backend != "none":
        _cache_write(cache_file, payload)
    payload["results"] = payload["results"][:max_results]
    return payload


def render(payload: dict[str, Any]) -> str:
    """Format the payload as a compact readable listing."""
    lines = [f"query: {payload['query']}"]
    meta = payload.get("judge") or {}
    if meta.get("model"):
        usage = meta.get("usage") or {}
        count = usage.get("input_tokens", 0)
        cost = meta.get("cost_usd")
        if cost == 0:
            price = " free"
        elif isinstance(cost, (int, float)):
            price = f" (${cost:.6f})"
        else:
            price = ""
        lines.append(
            f"judge: {meta['model']} via {meta.get('backend', '?')}"
            f"{price} ({count} in tokens)"
        )
    elif meta.get("error"):
        lines.append(f"judge: unavailable ({meta['error']})")
    results = payload.get("results") or []
    lines.append(
        f"results: {len(results)} of {payload.get('candidates', 0)} candidates"
    )
    if payload.get("cache") == "hit":
        lines.append("cache: hit (rerun with --no-cache for fresh retrieval)")
    elif payload.get("retrieval") == "brave-api":
        lines.append("engine: brave (exa unavailable or quota spent)")
    if payload.get("all_below_threshold"):
        lines.append("note: every candidate scored below threshold; top 2 kept")
    for n, row in enumerate(results, start=1):
        score = row.get("relevance")
        tag = f"{score:.2f}" if isinstance(score, float) else "raw"
        if row.get("weak"):
            tag += " weak"
        source = f" ({row['source']})" if row.get("source") else ""
        pick = row.get("best_pick")
        star = " *" if isinstance(pick, float) and pick >= 0.5 else ""
        lines.append(f"{n}. [{tag}]{source}{star} {row['title']}")
        lines.append(f"   {row['url']}")
        if row.get("snippet"):
            lines.append(f"   {row['snippet'][:240]}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Search the web, ranked by Jev")
    parser.add_argument("query")
    parser.add_argument("--max-results", type=int, default=8)
    parser.add_argument(
        "--judge",
        choices=[
            "auto",
            "opencode",
            "typesafe",
            "openrouter",
            "cloudflare",
            "vercel",
            "none",
        ],
        default=None,
        help="auto prefers the free OpenCode model, then configured paid providers",
    )
    parser.add_argument(
        "--engine",
        choices=["auto", "exa", "brave"],
        default=None,
        help="auto tries keyless Exa first, then Brave when BRAVE_API_KEY is set",
    )
    parser.add_argument(
        "--sources",
        default="web",
        help="comma list: web, reddit, x. X is indexed through mirrors, reddit directly",
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="bypass the 6 hour result cache and force fresh retrieval",
    )
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    backend = args.judge or os.environ.get("JEV_PROVIDER", "auto").lower()
    if backend not in {*JUDGES, "auto", "none"}:
        parser.error(f"unknown JEV_PROVIDER: {backend}")
    engine = args.engine or os.environ.get("JEV_SEARCH_ENGINE", "auto").lower()
    if engine not in ("auto", "exa", "brave"):
        parser.error(f"unknown JEV_SEARCH_ENGINE: {engine}")
    sources = tuple(s.strip() for s in args.sources.split(",") if s.strip())
    unknown = [s for s in sources if s != "web" and s not in SOURCE_FILTERS]
    if unknown:
        parser.error(f"unknown sources: {', '.join(unknown)}")
    try:
        payload = search(
            args.query,
            max_results=args.max_results,
            backend=backend,
            sources=sources,
            use_cache=not args.no_cache,
            engine=engine,
        )
    except RuntimeError as exc:
        print(f"jev-search: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(payload, indent=2) if args.json else render(payload))
    return 0


if __name__ == "__main__":
    sys.exit(main())
