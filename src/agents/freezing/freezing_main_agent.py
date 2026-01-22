from src.agents.base import BaseAgent
from src.utils.classifier.intents import IntentEnum
from src.tools.services.freezing_service import check_past_freezings, check_freezings, check_active_freezings
import json


class FreezingMainAgent(BaseAgent):
    def __init__(self, backend_tools, context_data, policy_loader, user_id):
        super().__init__(
            intent=IntentEnum.freezing,
            subintent=None,
            backend_tools=backend_tools,
            context_data=context_data,
            policy_loader=policy_loader,
            user_id=user_id
        )

    def get_data_from_api(self):
        all = check_freezings(user_id=self.user_id)
        active = check_active_freezings(user_id=self.user_id)
        past = check_past_freezings(user_id=self.user_id)

        result = {
            "freezings": all,
            "active_freezings": active,
            "past_freezings": past
        }

        result_string = json.dumps(result)

        return result_string

