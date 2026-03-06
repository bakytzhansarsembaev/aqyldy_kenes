from src.agents.base import BaseAgent
from src.utils.classifier.intents import IntentEnum, TaskProblemsSubIntentEnum
from src.tools.services.task_service import get_current_task, get_task_section
import json


class TaskEvaluationAgent(BaseAgent):
    def __init__(self, backend_tools, context_data, policy_loader, user_id,
                 previous_intent=None, previous_subintent=None):
        super().__init__(
            intent=IntentEnum.task_problems,
            subintent=TaskProblemsSubIntentEnum.task_evaluation,
            backend_tools=backend_tools,
            context_data=context_data,
            policy_loader=policy_loader,
            user_id=user_id,
            previous_intent=previous_intent,
            previous_subintent=previous_subintent
        )

    def get_data_from_api(self):
        if hasattr(self, '_cached_data'):
            return self._cached_data

        current_task = get_current_task(self.user_id)
        task_section = get_task_section(self.user_id)

        result = {}

        if current_task:
            result["current_task"] = current_task.get("task_text")
            result["task_type"] = current_task.get("task_type")
            result["task_id"] = current_task.get("task_id")
            result["has_subscription"] = current_task.get("has_subscription", True)
            result["personal_study_completed"] = current_task.get("personal_study_completed", False)
            result["decision_status"] = current_task.get("decision_status")
        else:
            result["current_task"] = None
            result["task_type"] = None
            result["task_id"] = None
            result["has_subscription"] = True
            result["personal_study_completed"] = False
            result["decision_status"] = None

        if task_section:
            result["total_tasks"] = task_section.get("total_tasks")
            result["completed_tasks"] = task_section.get("completed_tasks")
            result["current_task_index"] = task_section.get("current_task_index")

        self._cached_data = json.dumps(result, ensure_ascii=False)
        return self._cached_data
