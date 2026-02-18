from src.agents.base import BaseAgent
from src.utils.classifier.intents import IntentEnum, TaskProblemsSubIntentEnum
from src.tools.services.task_service import get_current_task
from src.tools.storage.state_store.redis_usage.state_repository import get_state_from_redis
import json


class TaskHelperHelperAgent(BaseAgent):
    def __init__(self, backend_tools, context_data, policy_loader, user_id):
        super().__init__(
            intent=IntentEnum.task_problems,
            subintent=TaskProblemsSubIntentEnum.task_problems,
            backend_tools=backend_tools,
            context_data=context_data,
            policy_loader=policy_loader,
            user_id=user_id
        )

    def get_data_from_api(self):
        # Получаем текущую задачу ученика
        current_task = get_current_task(self.user_id)

        if current_task:
            task_text = current_task.get('task_text') or ''
            print(f"[TaskHelper] Got task for user_id={self.user_id}: {task_text[:100]}...")
        else:
            print(f"[TaskHelper] No current task for user_id={self.user_id}")

        # Получаем state для проверки task_confirmed
        state = get_state_from_redis(self.user_id)
        task_confirmed = state.task_confirmed if state else False
        hints_given = state.hints_given if state else 0

        result = {
            "current_task": current_task.get("task_text") if current_task else None,
            "task_type": current_task.get("task_type") if current_task else None,
            "task_id": current_task.get("task_id") if current_task else None,
            "has_subscription": current_task.get("has_subscription", True) if current_task else True,
            "personal_study_completed": current_task.get("personal_study_completed", False) if current_task else False,
            "task_confirmed": task_confirmed,
            "hints_given": hints_given
        }

        return json.dumps(result, ensure_ascii=False)