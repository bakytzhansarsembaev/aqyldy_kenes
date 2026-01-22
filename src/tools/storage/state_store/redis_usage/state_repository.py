import json
from typing import Optional
from src.router.decision_router.graph_state import BotState
from src.tools.storage.state_store.redis_usage.redis_connection import redis_connection


def get_state_from_redis(user_id: str) -> Optional[BotState]:
    raw = redis_connection.get(user_id)

    if raw is None:
        return None

    data = json.loads(raw)

    return BotState.model_validate(data)


def save_state_into_redis(user_id, state: BotState):
    redis_connection.set(
        user_id,
        state.model_dump_json()
    )
