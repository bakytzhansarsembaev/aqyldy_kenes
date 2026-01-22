from src.agents.base import BaseAgent
from src.utils.classifier.intents import IntentEnum, CashbackSubIntentEnum
from src.tools.services.cashback_service import check_payments, check_payouts, cashback_sum, check_users_password
import json

class CashbackConditionsAgent(BaseAgent):
    def __init__(self, backend_tools, context_data, policy_loader, user_id):
        super().__init__(
            intent=IntentEnum.cashback,
            subintent=CashbackSubIntentEnum.conditions,
            backend_tools=backend_tools,
            context_data=context_data,
            policy_loader=policy_loader,
            user_id=user_id
        )

    def get_data_from_api(self):
        cash_sum = cashback_sum(self.user_id)
        auth_data = check_users_password(self.user_id)
        payments = check_payments(self.user_id)
        payouts = check_payouts(self.user_id)

        result = {
            "payments": payments,
            "payouts": payouts,
            "auth_data": auth_data,
            "cashback_sum": cash_sum,
        }

        result_string = json.dumps(result)

        return result_string