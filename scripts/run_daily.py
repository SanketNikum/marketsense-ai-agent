"""
Runs the full agent once and saves the result to disk.
Meant to be run on a schedule (e.g. once a day via GitHub Actions) -
the API then just serves this saved file instantly instead of
re-running the entire pipeline on every web request.
"""

import json
import os
from datetime import datetime, timezone

from agent.graph import graph

OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "latest_run.json")


def run_and_save():
    result = graph.invoke({})

    output = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "classified_movers": result.get("classified_movers", []),
        "stories": result.get("stories", []),
    }

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)

    print(f"Saved {len(output['classified_movers'])} movers, {len(output['stories'])} stories to {OUTPUT_PATH}")


if __name__ == "__main__":
    run_and_save()
