from src.router.decision_router.graph_state import BotState
from src.agents.registry import AGENT_REGISTRY


def agent_execution_node(state: BotState, policy_loader, backend_tools=None):
    key = (state.intent, state.subintent)
    AgentClass = AGENT_REGISTRY.get(key)

    if AgentClass is None:
        return ValueError(f"No Agent registered for intent/subintent {key}")

    agent = AgentClass(
        intent=state.intent,
        subintent=state.subintent,
        backend_tools=backend_tools,
        context_data=state.summary,
        policy_loader=policy_loader
    )

    state.response = agent.run_agent(user_message=state.user_message, summary=state.summary)
    return state