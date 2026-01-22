from src.router.decision_router.graph_state import BotState
from src.utils.classifier.summary import summarize
from src.agents.registry import AGENT_REGISTRY
from src.utils.classifier.classifier import classify


def summary_node(state: BotState):
    state.summary = summarize(
        state.usable_context
    )
    return state


def classifier_node(state: BotState):
    classify_result = classify(
        state.usable_context
    )
    state.intent, state.subintent = classify_result["intent"], classify_result["subintent"]

    return state


def agent_execution_node(
        state: BotState,
        policy_loader,
        backend_tools=None  # notice: TODO: разобраться с этим backend_tools недоразумением
):
    key = (state.intent, state.subintent)
    AgentClass = AGENT_REGISTRY.get(key)

    if AgentClass is None:
        return ValueError(f"No Agent registered for intent/subintent {key}")

    agent = AgentClass(
        # intent=state.intent,
        # subintent=state.subintent,
        context_data=state.summary,
        policy_loader=policy_loader,
        user_id=state.user_id,
        backend_tools=backend_tools
    )

    state.agent_answer = agent.run_agent(user_message=state.user_message, summary=state.summary)
    return state


def update_state_node(state: BotState):
    state.previous_intent = state.intent
    state.previous_subintent = state.previous_subintent

    return state
