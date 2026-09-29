# reddit-mention-collector

A private, single-user, **read-only** script that collects public post text from four crypto
subreddits so I can test one research question offline: *does a sudden rise in how often a
small-cap coin is mentioned precede a price move in that coin?* Non-commercial personal research.

This repository contains the complete code that would call the Reddit API, provided for
API-access review.

## Exactly what it does on Reddit

- Authenticates with the official OAuth API, read-only (PRAW, `reddit.read_only = True`).
- `GET /r/{subreddit}/new`, up to 100 posts, once per run, for four public subreddits:
  r/CryptoMoonShots, r/SatoshiStreetBets, r/Altcoin, r/CryptoCurrency.
- Intended cadence: one run per hour = 4 requests/run, **96 requests/day**. At least 60 seconds
  between subreddits; PRAW also honours Reddit's rate-limit headers.
- Descriptive User-Agent identifying the script and my Reddit username.
- No other endpoints: no search, no user endpoints, no comment crawling, no write endpoints.

## What it stores (local CSV, `data/reddit/<subreddit>.csv`)

`id, created_utc, title, selftext, permalink` — nothing else. **No usernames, no scores, no
comments.** Already-saved post ids are skipped, so nothing is stored twice.

## What it does NOT do

- Never posts, comments, votes, messages, awards, reports, or subscribes.
- Never touches private/quarantined subreddits, user profiles, post histories, or DMs.
- Never identifies, tracks, or profiles users.
- Raw text is not sold, published, or redistributed, and is **not used to train any AI/ML model**.
- Not a trading bot or commercial product. No trades are placed.
- Posts deleted or removed on Reddit are purged from local files on request.

## How the text is used (`entities.py`)

Titles and bodies are scanned for coin tickers/names (list in `data/coins.csv`), producing
per-coin, per-hour mention counts. Conservative rules to avoid false positives:

| Text | Match? |
|---|---|
| `$PENGU looks ready to run` | yes (cashtag) |
| `PENGU volume picking up` | yes (bare 4+ char uppercase ticker) |
| `pengu is cute` | no (lowercase bare ticker) |
| `one of the best` | no (3-char bare tickers never match) |
| `Pudgy Penguins holders rejoice` | yes (full name) |

Worked example: if `$PENGU` appears 1–2×/day for weeks, then 15× in one hour, that hour is
recorded as a mention burst. The coin's price over the following 24h (from exchange data) is
compared against price moves after randomly chosen non-burst hours. If bursts don't beat the
random baseline, the negative result is documented as such. Only aggregate counts feed the
analysis.

## Why not Devvit

I don't moderate the subreddits I need to read, so I can't install a Devvit app there, and the
analysis requires exporting public post text to run offline against exchange price history,
which Devvit's sandbox and fetch policy do not support.

## Setup

```
pip install -r requirements.txt
cp .env.example .env    # fill in credentials
python collector.py --subreddits CryptoMoonShots --limit 25
```

## Benefit to Redditors

None directly: a passive, non-interactive research tool with a very small footprint.
