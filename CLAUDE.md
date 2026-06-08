# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

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
