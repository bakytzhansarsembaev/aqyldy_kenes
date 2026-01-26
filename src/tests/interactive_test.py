"""
Интерактивный тест: ученик пишет → бот отвечает
Запуск: python -m src.tests.interactive_test
"""
from src.graph.graph_builder import build_graph
from src.utils.policies.policy_loader import PolicyLoader
from src.router.decision_router.graph_state import BotState
from src.utils.gpt_utils import usable_context


def create_test_context(history: list[dict]) -> list[dict]:
    """Преобразует историю сообщений в формат для классификатора"""
    formatted = []
    for msg in history:
        role = "assistant" if msg["sender"] == "bot" else "user"
        formatted.append({"role": role, "content": msg["text"]})
    return formatted


def run_interactive_test():
    """Интерактивный режим: вводим сообщение ученика, получаем ответ бота"""

    print("=" * 60)
    print("ИНТЕРАКТИВНЫЙ ТЕСТ ЧАТБОТА QALAN")
    print("=" * 60)
    print("Команды:")
    print("  /quit - выход")
    print("  /clear - очистить историю")
    print("  /state - показать текущий state")
    print("  /history - показать историю")
    print("=" * 60)

    # Инициализация
    policy_loader = PolicyLoader()
    graph = build_graph(policy_loader)

    # История диалога
    history = []
    user_id = "test_user_123"

    while True:
        try:
            # Ввод сообщения ученика
            user_input = input("\n[Ученик]: ").strip()

            if not user_input:
                continue

            # Команды
            if user_input == "/quit":
                print("Выход...")
                break

            if user_input == "/clear":
                history = []
                print("История очищена.")
                continue

            if user_input == "/history":
                print("\n--- История ---")
                for msg in history:
                    sender = "Ученик" if msg["sender"] == "pupil" else "Бот"
                    print(f"[{sender}]: {msg['text']}")
                print("--- Конец ---")
                continue

            if user_input == "/state":
                print("\nState будет показан после следующего сообщения")
                continue

            # Добавляем сообщение ученика в историю
            history.append({"sender": "pupil", "text": user_input})

            # Формируем контекст
            context_for_classifier = create_test_context(history)

            # Создаем BotState
            state = BotState(
                user_id=user_id,
                user_message=user_input,
                usable_context=context_for_classifier
            )

            # Прогоняем через граф
            print("\n[Обработка...]")
            result = graph.invoke(state)

            # LangGraph возвращает dict
            agent_answer = result.get("agent_answer") if isinstance(result, dict) else result.agent_answer
            intent = result.get("intent") if isinstance(result, dict) else result.intent
            subintent = result.get("subintent") if isinstance(result, dict) else result.subintent

            # Извлекаем текст ответа
            if agent_answer:
                if isinstance(agent_answer, dict):
                    bot_response = agent_answer.get("response", "Нет ответа")
                else:
                    bot_response = str(agent_answer)
            else:
                bot_response = "Ошибка: нет ответа от агента"

            # Добавляем ответ бота в историю
            history.append({"sender": "bot", "text": bot_response})

            # Выводим результат
            print(f"\n[Бот]: {bot_response}")
            print(f"\n--- Intent: {intent} | Subintent: {subintent} ---")

        except KeyboardInterrupt:
            print("\nПрервано пользователем")
            break
        except Exception as e:
            print(f"\nОшибка: {e}")
            import traceback
            traceback.print_exc()


def run_single_message_test(message: str, context: list[dict] = None):
    """Тест одного сообщения (для отладки)"""

    policy_loader = PolicyLoader()
    graph = build_graph(policy_loader)

    if context is None:
        context = [{"role": "user", "content": message}]

    state = BotState(
        user_id="test_user",
        user_message=message,
        usable_context=context
    )

    result = graph.invoke(state)

    # LangGraph возвращает dict, извлекаем данные
    intent = result.get("intent") if isinstance(result, dict) else result.intent
    subintent = result.get("subintent") if isinstance(result, dict) else result.subintent
    agent_answer = result.get("agent_answer") if isinstance(result, dict) else result.agent_answer

    print(f"Сообщение: {message}")
    print(f"Intent: {intent}")
    print(f"Subintent: {subintent}")
    print(f"Ответ: {agent_answer}")

    return result


if __name__ == "__main__":
    run_interactive_test()
