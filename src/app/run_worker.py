import requests
import json
import re
import time
from datetime import datetime
from src.router.decision_router.graph_state import BotState
from src.graph.graph_builder import build_graph
# from src.tools.services.push_reactions.pushes import check_message_for_push
from src.tools.storage.state_store.redis_usage.state_repository import get_state_from_redis, save_state_into_redis
from typing import Dict, Optional, Tuple
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


def extract_answer_from_response(raw_response) -> Tuple[str, str]:
    """
    Извлекает answer и decision из ответа агента.
    Обрабатывает: строку JSON, dict, вложенные структуры.
    """
    answer_text = ""
    decision = "response"

    # Если это строка - пробуем распарсить как JSON
    if isinstance(raw_response, str):
        # Убираем markdown code blocks если есть
        cleaned = raw_response.strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r'^```(?:json)?\s*', '', cleaned)
            cleaned = re.sub(r'\s*```$', '', cleaned)

        # Проверяем, похоже ли на JSON (начинается с { )
        if cleaned.startswith("{"):
            try:
                # Фиксируем невалидные JSON-эскейпы от LaTeX: \( \) \[ \] \frac и т.д.
                fixed = re.sub(r'\\([^"\\/bfnrtu])', r'\\\\\1', cleaned)
                parsed = json.loads(fixed)
                if isinstance(parsed, dict):
                    answer_text = parsed.get("answer") or ""
                    decision = parsed.get("decision", "response")
                else:
                    answer_text = raw_response
            except json.JSONDecodeError:
                # Если JSON не парсится - это обычный текст
                answer_text = raw_response
        else:
            answer_text = raw_response

    # Если это dict - извлекаем поля
    elif isinstance(raw_response, dict):
        answer_text = raw_response.get("answer") or ""
        decision = raw_response.get("decision", "response")

    else:
        answer_text = str(raw_response) if raw_response else ""

    return answer_text, decision


# Таймаут сессии в секундах (20 минут)
SESSION_TIMEOUT_SECONDS = 20 * 60
# Максимальное количество подсказок
MAX_HINTS = 5


def should_close_session(state: BotState, current_task_id: Optional[str]) -> Tuple[bool, str]:
    """Определяет, нужно ли закрыть сессию"""

    # 1. Все подсказки выданы
    if state.hints_given >= MAX_HINTS:
        return True, "max_hints_reached"

    # 2. Таймаут 20 минут
    if state.last_message_time:
        try:
            last_time = datetime.fromisoformat(state.last_message_time)
            if (datetime.now() - last_time).total_seconds() > SESSION_TIMEOUT_SECONDS:
                return True, "timeout_20min"
        except (ValueError, TypeError):
            pass

    # 3. Смена задания
    if state.confirmed_task_id and current_task_id and state.confirmed_task_id != current_task_id:
        return True, "task_changed"

    return False, ""


def reset_session(state: BotState) -> BotState:
    """Сбрасывает сессию и возвращает чистый state для нового цикла"""
    return BotState(
        user_id=state.user_id,
        user_message=state.user_message,
        usable_context=state.usable_context,
        # Сбрасываем все поля сессии:
        task_confirmed=False,
        confirmed_task_id=None,
        hints_given=0,
        current_hint_level=0,
        task_helper_active=False,
        session_closed=False,
        close_reason=None,
        session_start_time=None,
        last_message_time=None,
        # intent/subintent сбросятся при новой классификации
    )


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

    # Используем надёжный парсер для извлечения answer и decision
    answer_text, decision = extract_answer_from_response(raw_response)

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
                     "close_session": state.session_closed if state else False,
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
                ),
                session_start_time=datetime.now().isoformat(),
                last_message_time=datetime.now().isoformat()
            )
        else:
            # Проверяем нужно ли закрыть/сбросить сессию
            if old_state.session_closed:
                # Сессия была закрыта - начинаем заново с классификатора
                old_state = reset_session(old_state)
                old_state.session_start_time = datetime.now().isoformat()
                print(f"[SESSION] Reset for user_id={user_id}, starting fresh classification")

            old_state.user_message = input_json["question"]
            old_state.last_message_time = datetime.now().isoformat()
            # Обновляем контекст из rabbit — чтобы суммаризатор видел актуальную историю диалога
            old_state.usable_context = usable_context(
                context=input_json["context"],
                full_context=input_json["full_context"],
                session_context=input_json["session_context"]
            )
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
