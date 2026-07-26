"""
Data ingestion: fetches raw stock prices and news headlines.
No AI here on purpose - this is the deterministic "input" layer.
"""

import yfinance as yf
import feedparser

# A small watchlist to start with. Nifty 50 heavyweights, easy to sanity-check by eye.
WATCHLIST = ["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ICICIBANK.NS"]

# yfinance tickers don't match how news headlines refer to companies -
# news says "HDFC Bank", our data says "HDFCBANK.NS". This bridges the two.
TICKER_NAMES = {
    "RELIANCE.NS": "Reliance Industries",
    "TCS.NS": "TCS",
    "HDFCBANK.NS": "HDFC Bank",
    "INFY.NS": "Infosys",
    "ICICIBANK.NS": "ICICI Bank",
}

# Public RSS feeds - no API key needed.
NEWS_FEEDS = [
    "https://www.moneycontrol.com/rss/marketreports.xml",
    "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms",
]


def fetch_prices(tickers: list[str]) -> list[dict]:
    """
    Fetch the last 2 trading days of data per ticker and compute % change.
    Returns a list of dicts: [{"ticker": ..., "close": ..., "pct_change": ..., "volume": ...}, ...]
    """
    results = []

    for ticker in tickers:
        history = yf.Ticker(ticker).history(period="5d")

        if len(history) < 2:
            # Not enough data (e.g. new listing, or market holiday) - skip instead of crashing.
            continue

        latest = history.iloc[-1]
        previous = history.iloc[-2]

        pct_change = ((latest["Close"] - previous["Close"]) / previous["Close"]) * 100

        results.append({
            "ticker": ticker,
            "close": round(float(latest["Close"]), 2),
            "pct_change": round(float(pct_change), 2),
            "volume": int(latest["Volume"]),
        })

    return results


def fetch_news(feed_urls: list[str], limit_per_feed: int = 5) -> list[dict]:
    """
    Parse RSS feeds and return recent headlines.
    Returns a list of dicts: [{"title": ..., "summary": ..., "link": ...}, ...]
    """
    articles = []

    for url in feed_urls:
        parsed_feed = feedparser.parse(url)

        for entry in parsed_feed.entries[:limit_per_feed]:
            articles.append({
                "title": entry.get("title", ""),
                "summary": entry.get("summary", ""),
                "link": entry.get("link", ""),
            })

    return articles


if __name__ == "__main__":
    # Running this file directly (python data/ingest.py) lets us eyeball real output.
    print("=== PRICES ===")
    for row in fetch_prices(WATCHLIST):
        print(row)

    print("\n=== NEWS ===")
    for article in fetch_news(NEWS_FEEDS):
        print(article["title"])
