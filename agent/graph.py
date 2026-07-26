"""
Wires the node functions into an actual LangGraph state machine.
"""

from langgraph.graph import StateGraph, END

from agent.state import MarketSenseState
from agent.nodes import ingest_node, classify_node

graph_builder = StateGraph(MarketSenseState)

graph_builder.add_node("ingest", ingest_node)
graph_builder.add_node("classify", classify_node)

graph_builder.set_entry_point("ingest")
graph_builder.add_edge("ingest", "classify")
graph_builder.add_edge("classify", END)

graph = graph_builder.compile()


if __name__ == "__main__":
    result = graph.invoke({})

    print("Final state:")
    for mover in result["classified_movers"]:
        print(" ", mover)
