from src.router.decision_router.graph_state import BotState
from src.utils.classifier.classifier import classify


def classifier_node(state: BotState, usable_context):
    classify_result = classify(
        usable_context
    )
    state.intent, state.subintent = classify_result["intent"], classify_result["subintent"]

    return state
