"""
FastAPI backend exposing the MarketSense agent's latest daily run.
Serves a pre-computed result file instead of running the full agent
per-request - the pipeline runs on a schedule via scripts/run_daily.py.
"""

import json
import os

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

RESULT_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "latest_run.json")

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
    """Returns the latest saved agent run (see scripts/run_daily.py), not a live run."""
    if not os.path.exists(RESULT_PATH):
        raise HTTPException(status_code=503, detail="No daily run has completed yet")

    with open(RESULT_PATH, "r", encoding="utf-8") as f:
        result = json.load(f)

    # "context" is internal (used for RAGAS eval scoring) - strip it from the public response.
    for story in result.get("stories", []):
        story.pop("context", None)

    return result
