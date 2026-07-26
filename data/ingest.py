"""
Data ingestion: fetches raw stock prices and news headlines.
No AI here on purpose - this is the deterministic "input" layer.
"""

import yfinance as yf
import feedparser

# Nifty 50 constituents (approximate - index composition is rebalanced
# periodically, so this list may drift slightly from the live index).
TICKER_NAMES = {
    "ADANIENT.NS": "Adani Enterprises",
    "ADANIPORTS.NS": "Adani Ports",
    "APOLLOHOSP.NS": "Apollo Hospitals",
    "ASIANPAINT.NS": "Asian Paints",
    "AXISBANK.NS": "Axis Bank",
    "BAJAJ-AUTO.NS": "Bajaj Auto",
    "BAJFINANCE.NS": "Bajaj Finance",
    "BAJAJFINSV.NS": "Bajaj Finserv",
    "BEL.NS": "Bharat Electronics",
    "BHARTIARTL.NS": "Bharti Airtel",
    "CIPLA.NS": "Cipla",
    "COALINDIA.NS": "Coal India",
    "DRREDDY.NS": "Dr Reddy's Laboratories",
    "EICHERMOT.NS": "Eicher Motors",
    "GRASIM.NS": "Grasim Industries",
    "HCLTECH.NS": "HCL Technologies",
    "HDFCBANK.NS": "HDFC Bank",
    "HDFCLIFE.NS": "HDFC Life",
    "HEROMOTOCO.NS": "Hero MotoCorp",
    "HINDALCO.NS": "Hindalco Industries",
    "HINDUNILVR.NS": "Hindustan Unilever",
    "ICICIBANK.NS": "ICICI Bank",
    "INDUSINDBK.NS": "IndusInd Bank",
    "INFY.NS": "Infosys",
    "ITC.NS": "ITC",
    "JIOFIN.NS": "Jio Financial Services",
    "KOTAKBANK.NS": "Kotak Mahindra Bank",
    "LT.NS": "Larsen & Toubro",
    "M&M.NS": "Mahindra & Mahindra",
    "MARUTI.NS": "Maruti Suzuki",
    "NESTLEIND.NS": "Nestle India",
    "NTPC.NS": "NTPC",
    "ONGC.NS": "Oil & Natural Gas Corporation",
    "POWERGRID.NS": "Power Grid Corporation",
    "RELIANCE.NS": "Reliance Industries",
    "SBILIFE.NS": "SBI Life Insurance",
    "SHRIRAMFIN.NS": "Shriram Finance",
    "SBIN.NS": "State Bank of India",
    "SUNPHARMA.NS": "Sun Pharmaceutical",
    "TCS.NS": "Tata Consultancy Services",
    "TATACONSUM.NS": "Tata Consumer Products",
    "TATAMOTORS.NS": "Tata Motors",
    "TATASTEEL.NS": "Tata Steel",
    "TECHM.NS": "Tech Mahindra",
    "TITAN.NS": "Titan Company",
    "TRENT.NS": "Trent",
    "ULTRACEMCO.NS": "UltraTech Cement",
    "WIPRO.NS": "Wipro",
}

WATCHLIST = list(TICKER_NAMES.keys())

# Public RSS feeds - no API key needed.
NEWS_FEEDS = [
    "https://www.moneycontrol.com/rss/marketreports.xml",
    "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms",
]


def fetch_prices(tickers: list[str]) -> list[dict]:
    """
    Fetch the last 2 trading days of data for all tickers in one batched
    request (one call per ticker doesn't scale once the watchlist is 50 wide),
    and compute % change per ticker.
    Returns a list of dicts: [{"ticker": ..., "close": ..., "pct_change": ..., "volume": ...}, ...]
    """
    data = yf.download(tickers, period="5d", group_by="ticker", progress=False, threads=True)

    results = []

    for ticker in tickers:
        try:
            history = data[ticker].dropna()
        except KeyError:
            # yfinance sometimes silently drops a ticker it couldn't resolve.
            continue

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
