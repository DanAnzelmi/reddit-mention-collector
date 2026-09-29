"""
Maps free text to candidate coin ids, so mentions can be counted per coin.

Coin list: data/coins.csv with columns coin_id,symbol,name (a small sample is included;
the real research list has ~490 coins).

Matching rules (deliberately conservative -- false positives are worse than misses when
the goal is to count mentions):
  - `$TICKER` cashtag matches (case-insensitive, any ticker length).
  - A bare, case-SENSITIVE, uppercase ticker matches only if it is 4+ characters
    (1-3 character tickers like "ONE" or "AI" collide with ordinary words).
  - The coin's full name matches (case-insensitive) when known.

Examples:
    "$PENGU looks ready to run"        -> {"pudgy-penguins"}
    "PENGU volume picking up"          -> {"pudgy-penguins"}
    "pengu is cute"                    -> {}          (lowercase bare ticker)
    "one of the best"                  -> {}          (bare 3-char ticker never matches)
    "Pudgy Penguins holders rejoice"   -> {"pudgy-penguins"}
"""
import re
from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).resolve().parent / "data"
MIN_BARE_TICKER_LEN = 4


def _clean(value) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    return str(value).strip()


def build_matcher(coins_path: Path = DATA_DIR / "coins.csv"):
    coins = pd.read_csv(coins_path, dtype=str)
    entries = []
    for coin_id, symbol, name in zip(coins["coin_id"], coins["symbol"], coins["name"]):
        coin_id, symbol, name = _clean(coin_id), _clean(symbol).upper(), _clean(name)
        if not coin_id or not symbol:
            continue
        entries.append({
            "coin_id": coin_id,
            "cashtag_re": re.compile(rf"\$\s*{re.escape(symbol)}\b", re.IGNORECASE),
            "bare_re": (re.compile(rf"\b{re.escape(symbol)}\b")
                        if len(symbol) >= MIN_BARE_TICKER_LEN else None),
            "name_re": (re.compile(rf"\b{re.escape(name)}\b", re.IGNORECASE)
                        if len(name) >= 3 else None),
        })
    return entries


def match_text(text: str, matcher) -> set:
    if not text:
        return set()
    hits = set()
    for entry in matcher:
        if entry["cashtag_re"].search(text):
            hits.add(entry["coin_id"])
        elif entry["bare_re"] is not None and entry["bare_re"].search(text):
            hits.add(entry["coin_id"])
        elif entry["name_re"] is not None and entry["name_re"].search(text):
            hits.add(entry["coin_id"])
    return hits


if __name__ == "__main__":
    m = build_matcher()
    for s in ["$PENGU looks ready to run", "PENGU volume picking up", "pengu is cute",
              "one of the best", "Pudgy Penguins holders rejoice"]:
        print(f"{s!r:40} -> {sorted(match_text(s, m))}")
