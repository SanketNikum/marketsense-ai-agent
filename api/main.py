"""
FastAPI backend exposing the MarketSense agent as an HTTP endpoint.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from agent.graph import graph

app = FastAPI(title="MarketSense API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten to the real frontend domain before production
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/stories")
def get_stories():
    """Runs the full agent and returns today's classified movers + generated stories."""
    result = graph.invoke({})
    return {
        "classified_movers": result.get("classified_movers", []),
        "stories": result.get("stories", []),
    }
