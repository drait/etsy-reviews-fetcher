# Etsy Reviews Analyzer

CLI tool that fetches all reviews from an Etsy listing and uses Claude AI to generate actionable suggestions for improving your title, description, tags, photos, and pricing.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in your API keys
```

### API Keys

| Key | Where to get it |
|---|---|
| `ETSY_API_KEY` | [etsy.com/developers](https://www.etsy.com/developers) → create an app → copy the Keystring |
| `ANTHROPIC_API_KEY` | [console.anthropic.com](https://console.anthropic.com) |

## Usage

```bash
# Full Etsy URL
python main.py https://www.etsy.com/listing/1234567890/your-listing-title

# Or bare listing ID
python main.py 1234567890
```

## Output

The tool streams a structured improvement report covering:

1. **Title** — keywords to add/remove, search optimization
2. **Description** — missing info buyers ask about, structure and clarity
3. **Tags** — underused search terms based on what reviewers mention
4. **Photos** — inferred from review complaints or praise about visual expectations
5. **Pricing / Positioning** — value perception signals from reviews
6. **Top 3 Highest-Impact Changes** — the most lever-moving improvements

## How it works

1. Fetches listing details from the Etsy v3 API
2. Paginates through all reviews (up to 100 per request)
3. Sends everything to `claude-opus-4-8` with adaptive thinking
4. Streams the analysis to your terminal in real time
