"""
Node functions for the LangGraph agent. Each node takes the current state,
does one unit of work, and returns a dict of just the keys it wants to update.
"""

from agent.state import MarketSenseState
from agent.classify import filter_significant_movers, llm_classify_mover
from agent.generate import generate_story
from agent.guardrails import check_guardrails
from agent.cache import get_cached_story, store_in_cache
from rag.vectorstore import query_vectorstore
from data.ingest import fetch_prices, fetch_news, WATCHLIST, NEWS_FEEDS

MAX_RETRIES = 2


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


def generate_node(state: MarketSenseState) -> dict:
    """Writes a story for every mover the classifier judged worth_story=True."""
    movers_to_write = [m for m in state["classified_movers"] if m["worth_story"]]

    stories = []
    for mover in movers_to_write:
        cached_story = get_cached_story(mover)

        if cached_story is not None:
            story_text = cached_story
            # Retrieval is deterministic for the same mover, so re-querying (cheap,
            # no LLM call) recovers the context a cache hit would have used - needed
            # for RAGAS faithfulness scoring even when generation itself was skipped.
            context = [
                c["text"]
                for c in query_vectorstore(
                    f"{mover['ticker']} stock price movement explanation", n_results=2
                )
            ]
        else:
            story_text, context = generate_story(mover, state["news"])
            store_in_cache(mover, story_text)

        stories.append({"ticker": mover["ticker"], "story": story_text, "context": context})

    return {"stories": stories}


def guardrail_node(state: MarketSenseState) -> dict:
    """Checks every story against guardrails; flags for retry or falls back safely."""
    retry_count = state.get("retry_count", 0)
    movers_by_ticker = {m["ticker"]: m for m in state["classified_movers"]}

    checked_stories = []
    any_failed = False

    for story in state["stories"]:
        mover = movers_by_ticker[story["ticker"]]
        result = check_guardrails(story["story"], mover)

        if result["passed"]:
            checked_stories.append(story)
        elif retry_count < MAX_RETRIES:
            any_failed = True
            checked_stories.append(story)
        else:
            checked_stories.append({
                "ticker": story["ticker"],
                "story": f"We're unable to provide a verified explanation for {story['ticker']} right now.",
            })

    needs_retry = any_failed

    return {
        "stories": checked_stories,
        "retry_count": retry_count + 1 if needs_retry else retry_count,
        "needs_retry": needs_retry,
    }
