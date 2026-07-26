"""
Mover classification: decides which price moves are worth writing about.

Layer 1: a plain Python rule-based filter (cheap, instant, no API call).
Layer 2: an LLM reasoning pass on top of the survivors, using volume context
to catch cases a fixed threshold misses.
"""

import json
import os

from dotenv import load_dotenv
from groq import Groq

# Below this absolute % change, we don't even consider writing a story.
# Real markets: 1-2% is a reasonable "worth a look" threshold for large-caps.
SIGNIFICANCE_THRESHOLD_PCT = 0.4

# The fastest/cheapest Groq model - fine for a yes/no classification decision.
CLASSIFICATION_MODEL = "llama-3.1-8b-instant"

load_dotenv()  # reads .env into the environment so os.getenv() below can see it
_client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def filter_significant_movers(prices: list[dict]) -> list[dict]:
    """
    Keep only price rows whose absolute % change clears the threshold,
    sorted by magnitude of move (biggest movers first).
    """
    movers = [row for row in prices if abs(row["pct_change"]) >= SIGNIFICANCE_THRESHOLD_PCT]

    movers.sort(key=lambda row: abs(row["pct_change"]), reverse=True)

    return movers


def llm_classify_mover(mover: dict) -> dict:
    """
    Ask a cheap/fast LLM whether this price move is worth a written story,
    using volume as extra context a fixed % threshold can't see.

    Returns: {"worth_story": bool, "reason": str}
    """
    prompt = f"""You are a financial news editor deciding what deserves a headline.

Stock: {mover['ticker']}
Price change: {mover['pct_change']}%
Trading volume: {mover['volume']:,}

Decide if this move is significant enough for a short market-explainer story.
Respond ONLY with JSON in this exact shape, nothing else:
{{"worth_story": true or false, "reason": "one sentence why"}}
"""

    response = _client.chat.completions.create(
        model=CLASSIFICATION_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0,  # 0 = as deterministic as possible; we want consistent judgments, not creativity
    )

    raw_text = response.choices[0].message.content

    try:
        return json.loads(raw_text)
    except json.JSONDecodeError:
        # LLMs don't guarantee well-formed output. Fail safe instead of crashing the pipeline.
        return {"worth_story": False, "reason": f"Could not parse model output: {raw_text}"}


if __name__ == "__main__":
    from data.ingest import fetch_prices, WATCHLIST

    prices = fetch_prices(WATCHLIST)
    print("All prices:")
    for row in prices:
        print(" ", row)

    movers = filter_significant_movers(prices)
    print("\nSignificant movers (>= {}%):".format(SIGNIFICANCE_THRESHOLD_PCT))
    for row in movers:
        print(" ", row)

    print("\nLLM classification:")
    for row in movers:
        verdict = llm_classify_mover(row)
        print(f"  {row['ticker']}: {verdict}")
