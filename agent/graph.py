"""
Wires the node functions into an actual LangGraph state machine.
"""

from dotenv import load_dotenv
from langgraph.graph import StateGraph, END

# Loads LANGSMITH_API_KEY/LANGSMITH_TRACING/LANGSMITH_PROJECT from .env.
# LangGraph auto-traces every run once these are set - no other code needed.
load_dotenv()

from agent.state import MarketSenseState
from agent.nodes import ingest_node, classify_node, generate_node, guardrail_node


def route_after_classify(state: MarketSenseState) -> str:
    """Decides whether any mover is worth writing about, or the graph ends here."""
    has_story = any(m["worth_story"] for m in state["classified_movers"])
    return "generate" if has_story else "end"


def route_after_guardrail(state: MarketSenseState) -> str:
    """Loops back to generate on a guardrail failure (while retries remain), else ends."""
    return "generate" if state["needs_retry"] else "end"


graph_builder = StateGraph(MarketSenseState)

graph_builder.add_node("ingest", ingest_node)
graph_builder.add_node("classify", classify_node)
graph_builder.add_node("generate", generate_node)
graph_builder.add_node("guardrail", guardrail_node)

graph_builder.set_entry_point("ingest")
graph_builder.add_edge("ingest", "classify")
graph_builder.add_conditional_edges(
    "classify",
    route_after_classify,
    {"generate": "generate", "end": END},
)
graph_builder.add_edge("generate", "guardrail")
graph_builder.add_conditional_edges(
    "guardrail",
    route_after_guardrail,
    {"generate": "generate", "end": END},
)

graph = graph_builder.compile()


if __name__ == "__main__":
    result = graph.invoke({})

    print("Classified movers:")
    for mover in result["classified_movers"]:
        print(" ", mover)

    print("\nStories:")
    for story in result.get("stories", []):
        print(f"  [{story['ticker']}] {story['story']}")
