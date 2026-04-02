from src.agents.base import BaseAgent
from src.utils.classifier.intents import IntentEnum, CashbackSubIntentEnum
from src.tools.services.cashback_service import check_payments, check_payouts, cashback_sum, check_users_password, check_has_subscription
import json


UNSUBSCRIBED_CASHBACK_ANSWER = (
    "Qalan.kz – ақылы жазылымы бар оқушыларға тапсырма орындағаны үшін кэшбек береді. "
    "Сіз қазіргі таңда тегін оқуға тіркелгенсіз.\n\n"
    "Егер математикаңызды одан әрі дамытқыңыз келсе, ақылы жазылым арқылы қосымша мүмкіндіктерге қол жеткізе аласыз. "
    "Күн сайын есеп шығарып, тапсырмалар орындау арқылы кэшбек жинайсыз және түсінбеген есептеріңізді менторлардан сұрап, көмек ала аласыз.\n\n"
    "Егер ақылы жазылым алғыңыз келсе, осы жерге ата-анаңыздың телефон нөмірін қалдырсаңыз жеткілікті. Біз сізбен байланысамыз.☺️"
)


class CashbackWithdrawalAgent(BaseAgent):
    def __init__(self, backend_tools, context_data, policy_loader, user_id,
                 previous_intent=None, previous_subintent=None):
        super().__init__(
            intent=IntentEnum.cashback,
            subintent=CashbackSubIntentEnum.withdrawal,
            backend_tools=backend_tools,
            context_data=context_data,
            policy_loader=policy_loader,
            user_id=user_id,
            previous_intent=previous_intent,
            previous_subintent=previous_subintent
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

    def run_agent(self, user_message, summary):
        if not check_has_subscription(self.user_id):
            print(f"[CashbackWithdrawal] Blocked: no subscription for user_id={self.user_id}")
            return {
                "response": {"decision": "response", "answer": UNSUBSCRIBED_CASHBACK_ANSWER},
                "intent": self.intent,
                "subintent": self.subintent,
                "backend_data": None,
            }

        cash_data = cashback_sum(self.user_id)
        status = cash_data.get("active_cashback_request_status")

        if status == 10:
            return {
                "response": "Сіз кэшбек бойынша кезекте тұрсыз. Кезегіңіз келген уақытта қосымша арқылы ата-ана чатына дайын сілтеме жіберілетін болады және сізге ескерту хабарламасы келеді",
                "intent": self.intent,
                "subintent": self.subintent,
                "backend_data": None,
            }

        if status == 20:
            return {
                "response": "Сіздің кэшбек бойынша сілтемеңіз ата-ана чатына 00:00 уақытта жіберілді. Сілтеме жіберілген уақыттан бастап 24 сағатқа жарамды болады. Сілтемеге өту арқылы кэшбегіңізді ала аласыз",
                "intent": self.intent,
                "subintent": self.subintent,
                "backend_data": None,
            }

        try:
            auth_data = check_users_password(self.user_id)
            login = auth_data.get("login", "—")
        except Exception:
            login = "—"

        return {
            "response": (
                "Сәлеметсіз бе!☺️ Cashback-ке сұранымды жұмыс күндері 10:00 - 22:00 аралығында жібере аласыз.\n\n"
                "НҰСҚАУЛЫҚ:\n"
                "1. Qalan.kz сайтына өтіп, жүйеге кіріңіз:\n"
                f"Логин: {login}\n"
                "Құпия сөз: 12345678\n"
                "2. ПЕРСОНАЛДЫ ОҚЫТУ 🔜 КЭШБЕК бөліміне өтіңіз\n"
                "3. CASHBACK АЛУҒА СҰРАНЫМ батырмасын басып, кезекке тұра аласыз.🙌\n\n"
                "ЕСКЕРТУ:\n"
                "Сұранымды кэшбек 2000 теңгеден асқанда немесе оқу уақытыңыз аяқталғанда жібере аласыз.\n"
                "Сілтеме жіберілген уақыттан бастап 24 сағатқа жарамды болады және карта номеріне 18 жастан асқан, жарамдылық мерзімі өтпеген карта номерін енгізу керек"
            ),
            "intent": self.intent,
            "subintent": self.subintent,
            "backend_data": None,
        }