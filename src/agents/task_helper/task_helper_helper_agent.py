from src.agents.base import BaseAgent
from src.utils.classifier.intents import IntentEnum, TaskProblemsSubIntentEnum
from src.tools.services.task_service import get_current_task
from src.tools.storage.state_store.redis_usage.state_repository import get_state_from_redis, save_state_into_redis
import json


def _normalize_task_text(text: str) -> str:
    """Нормализует текст задачи для сравнения (убирает пробелы, переводы строк)."""
    if not text:
        return ""
    return " ".join(text.split()).strip().lower()


def _tasks_are_same(task1: str, task2: str) -> bool:
    """Сравнивает два текста задачи."""
    return _normalize_task_text(task1) == _normalize_task_text(task2)


class TaskHelperHelperAgent(BaseAgent):
    def __init__(self, backend_tools, context_data, policy_loader, user_id,
                 previous_intent=None, previous_subintent=None):
        super().__init__(
            intent=IntentEnum.task_problems,
            subintent=TaskProblemsSubIntentEnum.task_problems,
            backend_tools=backend_tools,
            context_data=context_data,
            policy_loader=policy_loader,
            user_id=user_id,
            previous_intent=previous_intent,
            previous_subintent=previous_subintent
        )

    def get_data_from_api(self):
        # Получаем state из Redis
        state = get_state_from_redis(self.user_id)

        # Получаем сохранённую задачу из state (если есть)
        saved_task_text = None
        saved_task_type = None
        if state and state.task_context:
            saved_task_text = state.task_context.get("task_text")
            saved_task_type = state.task_context.get("task_type")

        task_confirmed = state.task_confirmed if state else False
        hints_given = state.hints_given if state else 0

        # Получаем текущую задачу из API
        current_task = get_current_task(self.user_id)
        api_task_text = current_task.get("task_text") if current_task else None
        api_task_type = current_task.get("task_type") if current_task else None

        # Флаг смены задачи
        task_changed = False

        if api_task_text:
            print(f"[TaskHelper] Got task from API for user_id={self.user_id}: {api_task_text[:100]}...")

            # Проверяем: если есть сохранённая задача и она отличается от текущей
            if saved_task_text and task_confirmed:
                if not _tasks_are_same(saved_task_text, api_task_text):
                    task_changed = True
                    task_confirmed = False  # Сбрасываем подтверждение
                    hints_given = 0  # Сбрасываем счётчик подсказок
                    print(f"[TaskHelper] Task CHANGED for user_id={self.user_id}!")
                    print(f"[TaskHelper] Old task: {saved_task_text[:50]}...")
                    print(f"[TaskHelper] New task: {api_task_text[:50]}...")
                else:
                    print(f"[TaskHelper] Same task, continuing session for user_id={self.user_id}")

            # Сохраняем задачу в state если её ещё нет или она изменилась
            if state and (not saved_task_text or task_changed):
                state.task_context = {
                    "task_text": api_task_text,
                    "task_type": api_task_type,
                    "task_id": current_task.get("task_id")
                }
                if task_changed:
                    state.task_confirmed = False
                    state.hints_given = 0
                    state.current_hint_level = 0
                save_state_into_redis(self.user_id, state)
                print(f"[TaskHelper] Saved task to Redis for user_id={self.user_id}")
        else:
            print(f"[TaskHelper] No current task from API for user_id={self.user_id}")
            # Если API не вернул задачу, используем сохранённую (если есть)
            if saved_task_text:
                print(f"[TaskHelper] Using saved task from Redis: {saved_task_text[:100]}...")
                api_task_text = saved_task_text
                api_task_type = saved_task_type

        result = {
            "current_task": api_task_text,
            "task_type": api_task_type,
            "task_id": current_task.get("task_id") if current_task else None,
            "has_subscription": current_task.get("has_subscription", True) if current_task else True,
            "personal_study_completed": current_task.get("personal_study_completed", False) if current_task else False,
            "task_confirmed": task_confirmed,
            "hints_given": hints_given,
            "task_changed": task_changed  # Новый флаг для агента
        }

        return json.dumps(result, ensure_ascii=False)