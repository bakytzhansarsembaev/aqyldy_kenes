from src.agents.base import BaseAgent
from src.utils.classifier.intents import IntentEnum


class MentorAgent(BaseAgent):
    """
    Агент-переадресатор для вопросов, требующих человека-ментора.
    Используется когда классификатор определяет intent=mentor.

    Поведение:
    - Всегда возвращает decision="pass" с escalate_to_mentor=True
    - Объясняет ученику, что его вопрос передан ментору
    """

    def __init__(self, backend_tools, context_data, policy_loader, user_id,
                 previous_intent=None, previous_subintent=None):
        super().__init__(
            intent=IntentEnum.mentor,
            subintent=None,
            backend_tools=backend_tools,
            context_data=context_data,
            policy_loader=policy_loader,
            user_id=user_id,
            previous_intent=previous_intent,
            previous_subintent=previous_subintent
        )

    def get_data_from_api(self):
        """Mentor agent не требует данных из API"""
        return {}

    def run_agent(self, user_message, summary):
        """
        Всегда эскалирует к человеку-ментору.
        Не использует GPT для генерации ответа - возвращает фиксированное сообщение.
        """
        policy = self.load_policy()

        # Получаем сообщение из policy или используем дефолтное
        escalation_message = "Передаю твой вопрос наставнику. Он свяжется с тобой в ближайшее время."

        if hasattr(policy, 'policy') and hasattr(policy.policy, 'escalation_message'):
            escalation_message = policy.policy.escalation_message
        elif isinstance(policy.policy, dict):
            escalation_message = policy.policy.get(
                "escalation_message",
                escalation_message
            )

        response = {
            "decision": "pass",
            "answer": escalation_message,
            "escalate_to_mentor": True,
            "requires_human": True
        }

        return {
            "response": response,
            "intent": self.intent,
            "subintent": self.subintent
        }
