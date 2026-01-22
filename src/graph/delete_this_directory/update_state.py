from src.router.decision_router.graph_state import BotState


def update_state_node(state: BotState):
    state.previous_intent = state.intent
    state.previous_subintent = state.previous_subintent

    return state
