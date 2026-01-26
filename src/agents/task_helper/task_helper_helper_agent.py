from src.agents.base import BaseAgent
from src.utils.classifier.intents import IntentEnum, TaskProblemsSubIntentEnum
from src.tools.services.task_service import get_current_task
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
        
        result = {
            "current_task": current_task.get("task_text") if current_task else None,
            "task_type": current_task.get("task_type") if current_task else None,
            "has_subscription": current_task.get("has_subscription", True) if current_task else True,
            "personal_study_completed": current_task.get("personal_study_completed", False) if current_task else False
        }
        
        return json.dumps(result, ensure_ascii=False)