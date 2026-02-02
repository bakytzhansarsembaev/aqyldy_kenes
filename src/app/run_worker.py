import requests
import json
import time
from datetime import datetime
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

# Минимальный интервал между приветствиями (в минутах)
GREETING_COOLDOWN_MINUTES = 10


def _get_last_ml_greeting_time(full_context: str) -> Optional[datetime]:
    """Получает время последнего приветствия от ML из контекста."""
    try:
        context_list = json.loads(full_context) if isinstance(full_context, str) else full_context
        for msg in reversed(context_list):
            if msg.get("sender_type") == "ML" and msg.get("tag") == "greeting":
                date_str = msg.get("date")
                if date_str:
                    return datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
        return None
    except (json.JSONDecodeError, ValueError, TypeError):
        return None


def _is_greeting_on_cooldown(full_context: str) -> bool:
    """Проверяет, было ли недавно приветствие от ML."""
    last_greeting_time = _get_last_ml_greeting_time(full_context)
    if last_greeting_time is None:
        return False

    now = datetime.now()
    minutes_since_greeting = (now - last_greeting_time).total_seconds() / 60
    return minutes_since_greeting < GREETING_COOLDOWN_MINUTES


def run_event(input_json: Dict) -> Dict:
    response = run_push_event(input_json)
    if response is None:
        response = run_multi_agent_event(input_json)

    post_ml_response(response)
    return response


def post_ml_response(data: Dict):
    url = ML_RESPONSE.format(USABLE_BRANCH)
    print(f"[POST] sending to {url}")
    print(f"[POST] data: {data}")
    last_err = None
    for attempt in range(3):
        try:
            event_response = requests.post(
                url=url,
                headers={},
                json=data,
                timeout=10,
            )
            print(f"[POST] attempt={attempt+1} status={event_response.status_code}")
            if event_response.ok:
                print(f"[POST] success")
                return
            last_err = RuntimeError(f"Post failed: {event_response.status_code} body={event_response.text[:300]}")
            print(f"[POST] error: {last_err}")
        except requests.RequestException as e:
            last_err = e
            print(f"[POST] exception: {e}")

        # небольшой backoff; если совсем плохо - упадем и воркер сможет повторить
        time.sleep(0.5 * (attempt + 1))

    raise RuntimeError(f"Post failed after retries: {last_err}")


def map_intent_to_api_tag(intent: str, subintent: str = None) -> str:
    """
    Маппинг новых интентов на теги API (совместимость со старой версией).
    API ожидает теги: greeting, ok, completed, evaluation, done, promiss,
    freezing, cashback, returns, task_problems, mentor, spam и др.
    """
    # Сначала проверяем специфичные комбинации intent+subintent
    if subintent:
        subintent_str = str(subintent)
        intent_str = str(intent)

        # task_problems subintents
        if intent_str == "task_problems":
            if subintent_str == "task_problems":
                return "initiate_task_problems"
            if subintent_str == "change_task":
                return "task_problems"

        # freezing subintents
        if intent_str == "freezing":
            return "freezing"

        # cashback subintents
        if intent_str == "cashback":
            return "cashback"

        # support subintents
        if intent_str == "support":
            if subintent_str in ["tech_problems", "navigation"]:
                return "mentor"
            if subintent_str in ["motivation", "emotional"]:
                return "mentor"
            return "mentor"

    # Базовый маппинг по intent
    intent_mapping = {
        "neutral": "greeting",      # neutral → greeting (приветствия)
        "support": "mentor",        # support → mentor (API не знает support)
        "cashback": "cashback",     # без изменений
        "freezing": "freezing",     # без изменений
        "task_problems": "task_problems",  # без изменений
        "mentor": "mentor",         # без изменений
    }
    return intent_mapping.get(str(intent), "mentor")


def build_response_dict(input_json: Dict, state: Optional[BotState] = None) -> Dict:
    # agent_answer - это dict с ключами: response, intent, subintent
    agent_response = state.agent_answer or {}

    # Извлекаем текст ответа из response (может быть JSON-строкой или dict)
    raw_response = agent_response.get("response", "")

    # Парсим response - может быть: строка, JSON-строка, или уже dict
    answer_text = ""
    decision = "response"

    try:
        # Если строка - пробуем распарсить как JSON
        if isinstance(raw_response, str):
            try:
                parsed = json.loads(raw_response)
                if isinstance(parsed, dict):
                    answer_text = parsed.get("answer") or ""
                    decision = parsed.get("decision", "response")
                else:
                    answer_text = raw_response
            except json.JSONDecodeError:
                answer_text = raw_response
        # Если уже dict - извлекаем поля
        elif isinstance(raw_response, dict):
            answer_text = raw_response.get("answer") or ""
            decision = raw_response.get("decision", "response")
        else:
            answer_text = str(raw_response) if raw_response else ""
    except (TypeError, AttributeError):
        answer_text = str(raw_response) if raw_response else ""
        decision = "response"

    # Получаем confidence_score (если есть)
    confidence = state.confidence_score if state.confidence_score is not None else 1.0

    # Если агент не смог ответить - переключаем на ментора
    if decision == "pass" or answer_text is None:
        return {
            "answer": "",
            "tag": map_intent_to_api_tag(state.intent, state.subintent) if state.intent else "mentor",
            "prediction": confidence,
            "mode": True,  # Переключение на ментора
            "close_session": False,
            "session_id": input_json["session_id"],
            "pupil_id": input_json["pupil_id"],
            "sender_type": input_json["sender_type"],
            "full_context": input_json["full_context"],
            "context": input_json["context"],
            "question": state.user_message,
            "modified_message_time": input_json["modified_message_time"],
            "session_context": input_json["session_context"],
            "is_smart_suggestion": False
        }
        
    # Маппим интент на тег API
    api_tag = map_intent_to_api_tag(state.intent, state.subintent) if state.intent else "mentor"

    # Проверка на повторное приветствие
    if api_tag == "greeting" and _is_greeting_on_cooldown(input_json.get("full_context", "")):
        print(f"[Greeting] Skipping - recent greeting within {GREETING_COOLDOWN_MINUTES} minutes")
        return {
            "answer": "",
            "tag": api_tag,
            "prediction": confidence,
            "mode": False,  # Не отвечаем повторно
            "close_session": False,
            "session_id": input_json["session_id"],
            "pupil_id": input_json["pupil_id"],
            "sender_type": input_json["sender_type"],
            "full_context": input_json["full_context"],
            "context": input_json["context"],
            "question": state.user_message,
            "modified_message_time": input_json["modified_message_time"],
            "session_context": input_json["session_context"],
            "is_smart_suggestion": False
        }

    # mode=True означает бот отвечает (smart suggestion), mode=False означает передать ментору
    # Если confidence высокий и нет эскалации - бот отвечает сам
    bot_should_respond = confidence >= 0.7 and not state.escalate_to_mentor

    response_dict = {"answer": answer_text,
                     "tag": api_tag,
                     "prediction": confidence,
                     "mode": bot_should_respond,
                     "close_session": False,
                     "session_id": input_json["session_id"],
                     "pupil_id": input_json["pupil_id"],
                     "sender_type": input_json["sender_type"],
                     "full_context": input_json["full_context"],
                     "context": input_json["context"],
                     "question": state.user_message,
                     "modified_message_time": input_json["modified_message_time"],
                     "session_context": input_json["session_context"],
                     "is_smart_suggestion": True}

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
            # Сбрасываем флаги для нового сообщения
            old_state.escalate_to_mentor = False

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
