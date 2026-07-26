"""
Story generation: writes a short market explainer for one mover,
grounded in retrieved RAG context so the model isn't guessing from memory.
"""

import os

from dotenv import load_dotenv
from groq import Groq

from rag.vectorstore import query_vectorstore
from data.ingest import TICKER_NAMES

# A larger, stronger model than the classification tier - quality matters
# here because this is the text a recruiter/user actually reads.
GENERATION_MODEL = "llama-3.3-70b-versatile"

load_dotenv()
_client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def generate_story(mover: dict, news: list[dict]) -> str:
    """Writes a short explainer for a single mover, grounded in RAG context and recent news."""
    context_chunks = query_vectorstore(
        f"{mover['ticker']} stock price movement explanation", n_results=2
    )
    context_text = "\n\n".join(chunk["text"] for chunk in context_chunks)

    headlines_text = "\n".join(f"- {article['title']}" for article in news[:10])
    company_name = TICKER_NAMES.get(mover["ticker"], mover["ticker"])

    prompt = f"""You are a financial explainer writing for retail investors.

Stock: {mover['ticker']}, commonly referred to as "{company_name}" in news headlines
Price change: {mover['pct_change']}%
Trading volume: {mover['volume']:,}

Reference material (use only this to explain general concepts - do not invent facts):
{context_text}

Recent market headlines (use ONLY if genuinely relevant to "{company_name}" -
do not force a connection if none of these actually relate to it):
{headlines_text}

Write a 2-3 sentence explanation of this price move for a retail investor.
Do not give buy/sell advice or recommendations. If none of the headlines above
are clearly relevant to this stock, explain the move using the reference
material and volume context instead, and don't claim a specific news cause.
"""

    response = _client.chat.completions.create(
        model=GENERATION_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
    )

    return response.choices[0].message.content


if __name__ == "__main__":
    # Manufactured test input - today's real data has nothing worth_story=True,
    # so we test this node in isolation with a plausible example instead.
    test_mover = {
        "ticker": "HDFCBANK.NS",
        "pct_change": -2.8,
        "volume": 45000000,
    }
    test_news = [
        {"title": "HDFC Bank shares slide after Q1 profit misses analyst estimates"},
        {"title": "IT stocks rally on strong US tech earnings"},
    ]

    story = generate_story(test_mover, test_news)
    print(story)
