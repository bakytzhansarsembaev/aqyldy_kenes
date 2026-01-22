from src.graph.nodes import *
from src.router.decision_router.graph_state import BotState
from langgraph.graph import StateGraph, END
from functools import partial


def build_graph(policy_loader):
    # notice: добавить backend_tools, policy_loader, usable_context - в state
    graph = StateGraph(BotState)

    # summary -> classify -> agent -> update -> end
    graph.add_node("summary", summary_node)
    graph.add_node("classify", classifier_node)
    graph.add_node(
        "agent_execution",
        partial(
            agent_execution_node,
            policy_loader=policy_loader
        )
    )
    graph.add_node("update_state", update_state_node)

    # переходы
    graph.set_entry_point("summary")
    graph.add_edge("summary", "classify")
    graph.add_edge("classify", "agent_execution")
    graph.add_edge("agent_execution", "update_state")
    graph.add_edge("update_state", END)

    return graph.compile()
