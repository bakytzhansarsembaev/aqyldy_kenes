import requests
import json
import time
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
    last_err = None
    for attempt in range(3):
        try:
            event_response = requests.post(
                url=url,
                headers={},
                json=data,
                timeout=10,
            )
            if event_response.ok:
                return
            last_err = RuntimeError(f"Post failed: {event_response.status_code} body={event_response.text[:300]}")
        except requests.RequestException as e:
            last_err = e

        # небольшой backoff; если совсем плохо - упадем и воркер сможет повторить
        time.sleep(0.5 * (attempt + 1))

    raise RuntimeError(f"Post failed after retries: {last_err}")


def build_response_dict(input_json: Dict, state: Optional[BotState] = None) -> Dict:
    # agent_answer - это dict с ключами: response, intent, subintent
    agent_response = state.agent_answer or {}

    # Извлекаем текст ответа из response (может быть JSON-строкой)
    raw_response = agent_response.get("response", "")

    # Пробуем распарсить response как JSON (агент может вернуть {"decision": "...", "answer": "..."})
    try:
        parsed = json.loads(raw_response) if isinstance(raw_response, str) else raw_response
        answer_text = parsed.get("answer", raw_response)
        decision = parsed.get("decision", "response")
    except (json.JSONDecodeError, TypeError, AttributeError):
        answer_text = raw_response
        decision = "response"

    # Если агент не смог ответить - переключаем на ментора
    if decision == "pass" or answer_text is None:
        return {
            "answer": "",
            "tag": str(state.intent or "mentor"),
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
        
    response_dict = {"answer": answer_text,
                     "tag": str(state.intent or "mentor"),
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

        if isinstance(new_state, dict):
            new_state = BotState.model_validate(new_state)

        save_state_into_redis(user_id, new_state)
        return build_response_dict(input_json, new_state)

    except Exception as e:
        print("ERROR while processing event")
        print(f"user_id is: {user_id}")
        raise

    finally:
        current_input.current_input = None
