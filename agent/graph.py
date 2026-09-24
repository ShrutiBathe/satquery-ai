from typing import Literal

try:
    from langgraph.graph import StateGraph, START, END
except ModuleNotFoundError:
    StateGraph = None
    START = END = None

from .state import AgentState
from .query_understanding import understand_query as classify_query
from .validators import validate_agent_output


def understand_node(state: AgentState) -> AgentState:
    """
    Understand the user's query and determine the required task.
    """

    result = classify_query(
        query=state["query"],
        image_count=state["image_count"],
        metadata=state.get("metadata")
    )

    if not validate_agent_output(result):
        raise ValueError("AI Agent produced an invalid routing result.")

    return {
        "task": result["task"],
        "required_images": result["required_images"],
        "reason": result["reason"],
    }


def route_task(
    state: AgentState
) -> Literal[
    "vqa",
    "grounding",
    "change_detection",
    "optical_sar"
]:
    """
    Decide which specialist workflow should receive the request.
    """

    return state["task"]


def build_agent_graph():
    """
    Build the SatQuery AI Agent LangGraph.
    """

    graph = StateGraph(AgentState)

    # Query understanding node
    graph.add_node("understand_query", understand_node)

    # Start → Query Understanding
    graph.add_edge(START, "understand_query")

    # Query Understanding → Task Routing
    graph.add_conditional_edges(
        "understand_query",
        route_task,
        {
            "vqa": END,
            "grounding": END,
            "change_detection": END,
            "optical_sar": END,
        },
    )

    return graph.compile()


agent_graph = build_agent_graph() if StateGraph is not None else None


def run_graph(
    query: str,
    image_count: int,
    metadata: dict | None = None
) -> dict:
    """
    Run the AI Agent using LangGraph.
    """

    initial_state: AgentState = {
        "query": query,
        "image_count": image_count,
        "metadata": metadata,
    }

    if agent_graph is None:
        result = understand_node(initial_state)
    else:
        result = agent_graph.invoke(initial_state)

    return {
        "task": result["task"],
        "required_images": result["required_images"],
        "reason": result["reason"],
    }