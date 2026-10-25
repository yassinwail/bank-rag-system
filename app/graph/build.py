from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from app.graph.state import RAGState
from app.graph.nodes import (
    reset_turn_node,          # <-- new import
    access_check_node, route_node, sql_node, docs_node,
    chitchat_node, generate_answer_node
)


def after_access_check(state: RAGState) -> str:
    if state.get("access_denied"):
        return "generate_answer"
    return "route"


def route_decision(state: RAGState) -> list[str]:
    route = state["route"]
    if route == "sql":
        return ["sql_node"]
    elif route == "docs":
        return ["docs_node"]
    elif route == "both":
        return ["sql_node", "docs_node"]
    else:
        return ["chitchat_node"]


def build_graph():
    graph = StateGraph(RAGState)

    graph.add_node("reset_turn", reset_turn_node)       # <-- new: with the other add_node calls
    graph.add_node("access_check", access_check_node)
    graph.add_node("route", route_node)
    graph.add_node("sql_node", sql_node)
    graph.add_node("docs_node", docs_node)
    graph.add_node("chitchat_node", chitchat_node)
    graph.add_node("generate_answer", generate_answer_node)

    graph.set_entry_point("reset_turn")                 # <-- changed from "access_check"
    graph.add_edge("reset_turn", "access_check")        # <-- new

    graph.add_conditional_edges("access_check", after_access_check, {
        "route": "route",
        "generate_answer": "generate_answer",
    })

    graph.add_conditional_edges("route", route_decision, {
        "sql_node": "sql_node",
        "docs_node": "docs_node",
        "chitchat_node": "chitchat_node",
    })

    graph.add_edge("sql_node", "generate_answer")
    graph.add_edge("docs_node", "generate_answer")
    graph.add_edge("chitchat_node", "generate_answer")

    graph.add_edge("generate_answer", END)

    return graph.compile(checkpointer=MemorySaver())