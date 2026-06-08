# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

Behavioral guidelines to reduce common LLM coding mistakes. Merge with project-specific instructions as needed.

**Tradeoff:** These guidelines bias toward caution over speed. For trivial tasks, use judgment.

## 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them - don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

## 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

## 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it - don't delete it.

When your changes create orphans:
- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

## 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:
- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:
```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

---

**These guidelines are working if:** fewer unnecessary changes in diffs, fewer rewrites due to overcomplication, and clarifying questions come before implementation rather than after mistakes.

---

## Project

CLI tool that fetches all reviews from an Etsy listing and streams an improvement analysis using Claude.

## Setup & Usage

```bash
pip install -r requirements.txt
cp .env.example .env   # fill in ETSY_API_KEY and ANTHROPIC_API_KEY
python main.py <listing_url_or_id>
```

Accepts either a full Etsy URL (`https://www.etsy.com/listing/123456/title`) or a bare listing ID.

## Architecture

Single-file tool (`main.py`):
- `extract_listing_id` — parses listing ID from URL or raw integer string
- `fetch_listing` — `GET /v3/application/listings/{id}` with `x-api-key` header
- `fetch_all_reviews` — paginates `GET /v3/application/listings/{id}/reviews` (limit 100, offset-based) until all reviews are collected
- `analyze` — sends listing + reviews to `claude-opus-4-8` with adaptive thinking, streams output to stdout

## APIs

- **Etsy v3**: `https://openapi.etsy.com/v3/application/` — auth via `x-api-key` header (no OAuth needed for public listing data)
- **Anthropic**: standard Python SDK, `claude-opus-4-8`, adaptive thinking, streaming via `.text_stream`
