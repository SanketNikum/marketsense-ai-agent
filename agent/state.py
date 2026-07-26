"""
The shared state that flows through every node in the LangGraph agent.
Every node reads from this and writes new keys onto it.
"""

from typing import TypedDict


class MarketSenseState(TypedDict):
    raw_prices: list[dict]
    news: list[dict]
    movers: list[dict]
    classified_movers: list[dict]
    stories: list[dict]
