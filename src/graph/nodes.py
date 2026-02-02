from src.router.decision_router.graph_state import BotState
from src.utils.classifier.summary import summarize
from src.agents.registry import AGENT_REGISTRY
from src.utils.classifier.classifier import classify
from src.utils.classifier.intents import IntentEnum, TaskProblemsSubIntentEnum


def _get_context_with_current_message(state: BotState) -> list:
    """Добавляет текущее сообщение пользователя к контексту для классификации."""
    context = state.usable_context or []
    # Добавляем текущее сообщение пользователя в конец контекста
    if state.user_message:
        context = context + [{"role": "user", "content": state.user_message}]
    return context


def summary_node(state: BotState):
    # Используем контекст с текущим сообщением
    context_with_message = _get_context_with_current_message(state)
    state.summary = summarize(context_with_message)
    return state


def classifier_node(state: BotState):
    # Используем контекст с текущим сообщением для классификации
    context_with_message = _get_context_with_current_message(state)

    # Передаём предыдущий интент в классификатор для контекста
    classify_result = classify(context_with_message, previous_intent=state.previous_intent)

    state.intent = classify_result["intent"]
    state.subintent = classify_result["subintent"]
    state.confidence_score = classify_result.get("confidence")

    return state


def agent_execution_node(
        state: BotState,
        policy_loader,
        backend_tools=None
):
    key = (state.intent, state.subintent)
    AgentClass = AGENT_REGISTRY.get(key)

    if AgentClass is None:
        return ValueError(f"No Agent registered for intent/subintent {key}")

    agent = AgentClass(
        context_data=state.summary,
        policy_loader=policy_loader,
        user_id=state.user_id,
        backend_tools=backend_tools
    )

    # Запуск агента
    agent_result = agent.run_agent(user_message=state.user_message, summary=state.summary)
    state.agent_answer = agent_result

    # ============================================
    # Task Helper специфическая обработка
    # ============================================
    if state.intent == IntentEnum.task_problems:
        try:
            _process_task_helper_response(state, agent_result, backend_tools)
        except Exception as e:
            print(f"[Task Helper] State update error: {e}")
            import traceback
            traceback.print_exc()

    # ============================================
    # Mentor эскалация
    # ============================================
    if state.intent == IntentEnum.mentor:
        state.escalate_to_mentor = True
        print(f"[Mentor] Escalation for user_id={state.user_id}")

    return state


def _process_task_helper_response(state: BotState, agent_result: dict, backend_tools: dict):
    """
    Обработка ответа Task Helper агента.

    Включает:
    - Обновление состояния Task Helper
    - Обработку LaTeX формул
    - Логирование
    """
    import json
    from src.utils.latex_processor import fix_latex_formatting, validate_latex, count_formulas

    response_data = agent_result.get("response", {})

    # Если response - JSON строка, парсим её
    if isinstance(response_data, str):
        try:
            parsed = json.loads(response_data)
            if isinstance(parsed, dict):
                response_data = parsed
                agent_result["response"] = parsed  # Обновляем на dict
        except (json.JSONDecodeError, TypeError):
            pass  # Оставляем как строку

    # Извлекаем answer_text
    if isinstance(response_data, dict):
        answer_text = response_data.get("answer", "") or ""
    else:
        answer_text = response_data if response_data else ""

    # Обновляем Task Helper состояние
    state.task_helper_active = True

    # Получаем hint_level из response если есть
    if isinstance(response_data, dict):
        hint_level = response_data.get("hint_level", 0)
        state.current_hint_level = hint_level
        state.escalate_to_mentor = response_data.get("escalate_to_mentor", False)

        # Увеличиваем счётчик подсказок
        if hint_level > 0:
            state.hints_given += 1

    # Сохраняем контекст задачи
    if state.task_context is None and backend_tools:
        state.task_context = {
            "task_text": backend_tools.get("current_task") or backend_tools.get("task_text"),
            "task_type": backend_tools.get("task_type"),
            "task_id": backend_tools.get("task_id")
        }

    # ============================================
    # LaTeX обработка
    # ============================================
    if answer_text and validate_latex(answer_text):
        formulas_count = count_formulas(answer_text)
        print(f"[LaTeX] Processing {formulas_count} formula(s) for user_id={state.user_id}")

        answer_text = fix_latex_formatting(answer_text)

        # Обновляем ответ
        if isinstance(response_data, dict):
            response_data["answer"] = answer_text
            agent_result["response"] = response_data
        else:
            agent_result["response"] = answer_text

        state.agent_answer = agent_result


def update_state_node(state: BotState):
    state.previous_intent = state.intent
    state.previous_subintent = state.subintent

    return state
