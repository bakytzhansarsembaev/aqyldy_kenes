from src.agents.base import BaseAgent
from src.utils.classifier.intents import IntentEnum, SupportSubIntentEnum


class SupportEmotionalAgent(BaseAgent):
    def __init__(self, backend_tools, context_data, policy_loader, user_id):
        super().__init__(
            intent=IntentEnum.support,
            subintent=SupportSubIntentEnum.emotional,
            backend_tools=backend_tools,
            context_data=context_data,
            policy_loader=policy_loader,
            user_id=user_id
        )

    def get_data_from_api(self):
        return {}
