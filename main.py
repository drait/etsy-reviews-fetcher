#!/usr/bin/env python3
"""Fetch all reviews from an Etsy listing and analyze them with Claude."""
import os
import re
import sys

import anthropic
import requests
from dotenv import load_dotenv

load_dotenv()


def extract_listing_id(arg: str) -> str:
    match = re.search(r"/listing/(\d+)", arg)
    if match:
        return match.group(1)
    if arg.isdigit():
        return arg
    sys.exit(f"Error: cannot extract a listing ID from '{arg}'")


def fetch_listing(listing_id: str) -> dict:
    resp = requests.get(
        f"https://openapi.etsy.com/v3/application/listings/{listing_id}",
        headers={"x-api-key": os.environ["ETSY_API_KEY"]},
    )
    resp.raise_for_status()
    return resp.json()


def fetch_all_reviews(listing_id: str) -> list[dict]:
    reviews = []
    offset = 0
    limit = 100
    while True:
        resp = requests.get(
            f"https://openapi.etsy.com/v3/application/listings/{listing_id}/reviews",
            headers={"x-api-key": os.environ["ETSY_API_KEY"]},
            params={"limit": limit, "offset": offset},
        )
        resp.raise_for_status()
        data = resp.json()
        batch = data.get("results", [])
        reviews.extend(batch)
        if len(reviews) >= data["count"] or len(batch) < limit:
            break
        offset += limit
    return reviews


def analyze(listing: dict, reviews: list[dict]) -> None:
    client = anthropic.Anthropic()

    text_reviews = [r for r in reviews if r.get("review", "").strip()]
    review_lines = "\n".join(
        f"- ({r['rating']}/5) {r['review'].strip()}" for r in text_reviews
    ) or "(no text reviews)"

    price_str = "N/A"
    if listing.get("price"):
        p = listing["price"]
        amount = p.get("amount", 0) / p.get("divisor", 100)
        price_str = f"{amount:.2f} {p.get('currency_code', '')}"

    prompt = f"""You are an Etsy listing optimization expert. Analyze this listing and its customer reviews, then provide specific, actionable suggestions to build a better listing.

LISTING:
Title: {listing.get('title', 'N/A')}
Description: {(listing.get('description') or 'N/A')[:3000]}
Tags: {', '.join(listing.get('tags') or [])}
Materials: {', '.join(listing.get('materials') or [])}
Price: {price_str}

REVIEWS ({len(reviews)} total, {len(text_reviews)} with text):
{review_lines[:8000]}

Provide suggestions in these sections:
1. **Title** — keywords to add/remove, search optimization
2. **Description** — missing info buyers ask about, structure, clarity
3. **Tags** — underused search terms based on what reviewers mention
4. **Photos** — inferred from complaints or praise about visual expectations
5. **Pricing / Positioning** — if reviews hint at value perception issues
6. **Top 3 Highest-Impact Changes** — the most lever-moving improvements

Be specific and concrete. Quote actual reviews where relevant."""

    with client.messages.stream(
        model="claude-opus-4-8",
        max_tokens=2048,
        thinking={"type": "adaptive"},
        messages=[{"role": "user", "content": prompt}],
    ) as stream:
        for text in stream.text_stream:
            print(text, end="", flush=True)
    print()


def main():
    if len(sys.argv) != 2:
        sys.exit("Usage: python main.py <listing_url_or_id>")

    listing_id = extract_listing_id(sys.argv[1])

    print(f"Fetching listing {listing_id}...", flush=True)
    listing = fetch_listing(listing_id)

    print("Fetching reviews...", flush=True)
    reviews = fetch_all_reviews(listing_id)
    text_count = sum(1 for r in reviews if r.get("review", "").strip())
    print(f"Found {len(reviews)} reviews ({text_count} with text)\n", flush=True)

    print(f"=== {listing.get('title', listing_id)} ===\n", flush=True)
    analyze(listing, reviews)


if __name__ == "__main__":
    main()
