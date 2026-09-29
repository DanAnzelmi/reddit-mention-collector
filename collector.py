"""
Read-only collector of public Reddit posts, for offline research on coin-mention volume.

What this script does on Reddit (and nothing else):
  - Authenticates with the official OAuth API in read-only mode (PRAW, `read_only = True`).
  - For each of a small, fixed list of PUBLIC subreddits, makes ONE request per run to the
    "new" listing (GET /r/{subreddit}/new), up to 100 posts.
  - Waits at least 60 seconds between subreddits. PRAW additionally honours Reddit's
    rate-limit headers on its own.

What it stores locally, per post: id, creation time, title, body text, permalink.
It does not store usernames, scores, or comments, and it never writes to Reddit
(no posting, commenting, voting, messaging, subscribing, or reporting).

Intended cadence: one run per hour, i.e. 4 requests/run, 96 requests/day.

Usage:
    python collector.py
    python collector.py --subreddits CryptoMoonShots --limit 25   # smoke test
"""
import argparse
import os
import sys
import time
from pathlib import Path

import pandas as pd
import praw
from dotenv import load_dotenv

OUT_DIR = Path(__file__).resolve().parent / "data" / "reddit"
DEFAULT_SUBREDDITS = ["CryptoMoonShots", "SatoshiStreetBets", "Altcoin", "CryptoCurrency"]
COLUMNS = ["id", "created_utc", "title", "selftext", "permalink"]
MAX_LIMIT = 100
SECONDS_BETWEEN_SUBREDDITS = 60


def load_existing(path: Path):
    if not path.exists():
        return None
    df = pd.read_csv(path, dtype={"id": str})
    if df.empty:
        return None
    df["created_utc"] = pd.to_datetime(df["created_utc"], utc=True)
    return df


def fetch_subreddit(reddit, name: str, limit: int) -> pd.DataFrame:
    rows = []
    for post in reddit.subreddit(name).new(limit=limit):
        rows.append({
            "id": post.id,
            "created_utc": pd.Timestamp(float(post.created_utc), unit="s", tz="UTC"),
            "title": post.title,
            "selftext": post.selftext or "",
            "permalink": f"https://reddit.com{post.permalink}",
        })
    return pd.DataFrame(rows, columns=COLUMNS)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--subreddits", nargs="+", default=DEFAULT_SUBREDDITS)
    parser.add_argument("--limit", type=int, default=MAX_LIMIT,
                        help=f"Posts requested per subreddit per run (capped at {MAX_LIMIT})")
    args = parser.parse_args()
    limit = min(args.limit, MAX_LIMIT)

    load_dotenv()
    client_id = os.getenv("REDDIT_CLIENT_ID")
    client_secret = os.getenv("REDDIT_CLIENT_SECRET")
    user_agent = os.getenv("REDDIT_USER_AGENT")
    if not client_id or not client_secret or not user_agent:
        print("Missing Reddit credentials. Set REDDIT_CLIENT_ID / REDDIT_CLIENT_SECRET / "
              "REDDIT_USER_AGENT in a .env file (see .env.example).")
        sys.exit(1)

    reddit = praw.Reddit(client_id=client_id, client_secret=client_secret, user_agent=user_agent)
    reddit.read_only = True

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for i, name in enumerate(args.subreddits):
        if i > 0:
            time.sleep(SECONDS_BETWEEN_SUBREDDITS)
        path = OUT_DIR / f"{name}.csv"
        existing = load_existing(path)
        fetched = fetch_subreddit(reddit, name, limit)
        if fetched.empty:
            print(f"r/{name}: no posts fetched")
            continue
        if existing is not None:
            new_df = fetched[~fetched["id"].isin(existing["id"])]
            combined = pd.concat([existing, new_df]) if not new_df.empty else existing
        else:
            new_df = fetched
            combined = fetched
        combined = combined.sort_values("created_utc")
        combined.to_csv(path, index=False)
        print(f"r/{name}: +{len(new_df)} new posts, {len(combined)} total -> {path}")


if __name__ == "__main__":
    main()
