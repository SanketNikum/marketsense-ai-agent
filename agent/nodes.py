"""
Node functions for the LangGraph agent. Each node takes the current state,
does one unit of work, and returns a dict of just the keys it wants to update.
"""

from agent.state import MarketSenseState
from agent.classify import filter_significant_movers, llm_classify_mover
from data.ingest import fetch_prices, fetch_news, WATCHLIST, NEWS_FEEDS


def ingest_node(state: MarketSenseState) -> dict:
    """Fetches raw prices and news headlines, writes both onto the state."""
    prices = fetch_prices(WATCHLIST)
    news = fetch_news(NEWS_FEEDS)
    return {"raw_prices": prices, "news": news}


def classify_node(state: MarketSenseState) -> dict:
    """Filters significant movers and runs the LLM verdict on each."""
    movers = filter_significant_movers(state["raw_prices"])

    classified = []
    for mover in movers:
        verdict = llm_classify_mover(mover)
        classified.append({**mover, **verdict})

    return {"movers": movers, "classified_movers": classified}
