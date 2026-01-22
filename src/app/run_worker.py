import requests
import json
from src.router.decision_router.graph_state import BotState
from src.graph.graph_builder import build_graph
# from src.tools.services.push_reactions.pushes import check_message_for_push
from src.tools.storage.state_store.redis_usage.state_repository import get_state_from_redis, save_state_into_redis
from typing import Dict, Optional
from src.runtime.rabbit_input import current_input
from src.configs.settings import ML_RESPONSE, USABLE_BRANCH
from src.utils.policies.policy_loader import PolicyLoader
from src.utils.gpt_utils import usable_context
graph = build_graph(policy_loader=PolicyLoader())


def run_event(input_json: Dict) -> Dict:
    response = run_push_event(input_json)
    if response is None:
        response = run_multi_agent_event(input_json)

    post_ml_response(response)
    return response


def post_ml_response(data: Dict):
    url = ML_RESPONSE.format(USABLE_BRANCH)
    event_response = requests.post(
        url=url,
        headers={},
        json=data
    )

    if not event_response.ok:
        raise RuntimeError(f"Post failed: {event_response.status_code}")


def build_response_dict(input_json: Dict, state: Optional[BotState] = None) -> Dict:
    # Парсим JSON-ответ от агента
    try:
        agent_response = json.loads(state.agent_answer)
        answer_text = agent_response.get("answer", state.agent_answer)
        decision = agent_response.get("decision", "response")

        # ------------------------------------------------------------------------------------------------тут надо подумать 
        # Если агент не смог ответить - переключаем на ментора
        if decision == "pass" or answer_text is None:
            return {
                "answer": "",
                "tag": {
                    "intent": state.intent,
                    "subintent": state.subintent
                },
                "prediction": 1,
                "mode": True,  # Переключение на ментора
                "close_session": False,
                "session_id": input_json["session_id"],
                "pupil_id": input_json["pupil_id"],
                "sender_type": input_json["sender_type"],
                "full_context": input_json["full_context"],
                "context": input_json["context"],
                "question": state.user_message,
                "modified_message_time": input_json["modified_message_time"],
                "session_context": input_json["session_context"]
            }
            
    except (json.JSONDecodeError, TypeError, AttributeError):
        # Если не JSON или ошибка парсинга - используем как есть
        answer_text = state.agent_answer
        decision = "response"
        
    response_dict = {"answer": answer_text,
                     "tag": {"intent": state.intent,
                             "subintent": state.subintent}, # notice: возможно стоит обернуть в str
                     "prediction": 1, # decision_score - добавить
                     "mode": False, # - добавить desicion_score для ответа агентов
                     "close_session": False, # - добавить decision_score для закрытия сессии
                     "session_id": input_json["session_id"],
                     "pupil_id": input_json["pupil_id"],
                     "sender_type": input_json["sender_type"],
                     "full_context": input_json["full_context"],
                     "context": input_json["context"],
                     "question": state.user_message,
                     "modified_message_time": input_json["modified_message_time"],
                     "session_context": input_json["session_context"]}

    return response_dict


def run_push_event(input_json: Dict) -> Optional[Dict]:
    # return check_message_for_push(input_json)
    return None


def run_multi_agent_event(input_json: Dict) -> Dict:
    user_id = input_json["user_id"]
    old_state = get_state_from_redis(user_id)

    current_input.current_input = input_json

    try:
        if old_state is None:
            old_state = BotState(
                user_id=user_id,
                user_message=input_json["question"],
                usable_context=usable_context(
                    context=input_json["context"],
                    full_context=input_json["full_context"],
                    session_context=input_json["session_context"]
                )
            )
        else:
            old_state.user_message = input_json["question"]

        new_state = graph.invoke(old_state)

        save_state_into_redis(user_id, new_state)
        return build_response_dict(input_json, new_state)

    except Exception as e:
        print("ERROR while processing event")
        print(f"user_id is: {user_id}")
        raise

    finally:
        current_input.current_input = None

