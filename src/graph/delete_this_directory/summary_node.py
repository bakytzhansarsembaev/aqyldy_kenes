from src.router.decision_router.graph_state import BotState
from src.utils.classifier.summary import summarize


def summary_node(state: BotState, usable_context):
    state.summary = summarize(
        # summarize pustoi
    )
    return state