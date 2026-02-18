from src.agents.base import BaseAgent
from src.utils.classifier.intents import IntentEnum, FreezingSubIntentEnum


class FreezingStatusCheckerAgent(BaseAgent):
    def __init__(self, backend_tools, context_data, policy_loader, user_id,
                 previous_intent=None, previous_subintent=None):
        super().__init__(
            intent=IntentEnum.freezing,
            subintent=FreezingSubIntentEnum.freezing_status_check,
            backend_tools=backend_tools,
            context_data=context_data,
            policy_loader=policy_loader,
            user_id=user_id,
            previous_intent=previous_intent,
            previous_subintent=previous_subintent
        )

    def get_data_from_api(self):
        return {}
