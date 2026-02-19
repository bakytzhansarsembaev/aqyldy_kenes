import requests, json
from src.configs.settings import USER_CASHBACKS, headers1, USER_LOGIN_PASSWORDS_URL, USER_PAYMENTS, USER_PAYOUTS, USE_MOCK_SERVICES

if USE_MOCK_SERVICES:
    from src.tools.services.mock_services import (
        mock_cashback_sum, mock_check_users_password,
        mock_check_payments, mock_check_payouts
    )


def cashback_sum(user_id: str):
    # какая сумма доступна для снятия
    if USE_MOCK_SERVICES:
        return mock_cashback_sum(user_id)

    url = USER_CASHBACKS.format(user_id)
    try:
        response = requests.get(url=url, headers=headers1)

    except:
        raise ConnectionError(f"Cashback service not responding in {cashback_sum.__name__}")

    if response.status_code == 200:
        data = response.json()
        cash_sum = data["cashbackSum"] - data["payoutSum"]
        return {"cashback_sum": cash_sum}

    else:
        raise ConnectionError(f"Cashback service {cashback_sum.__name__} doesn't work. status_code is: {response.status_code}")


def check_users_password(user_id: str):
    # логин и пароль user-а
    if USE_MOCK_SERVICES:
        return mock_check_users_password(user_id)

    url = USER_LOGIN_PASSWORDS_URL.format(str(user_id))
    try:
        response = requests.get(url=url, headers=headers1)

    except:
        raise ConnectionError(f"Cashback service not responding in {check_users_password.__name__}")

    if response.status_code == 200:
        data = response.json()

        return {"login": data["phoneNumber"], "password": data["password"]}

    else:
        raise ConnectionError(f"Cashback service {check_users_password.__name__} doesn't work. status_code is: {response.status_code}")


def check_payments(user_id: str):
    # список начислений кэшбэка с датой и суммой
    if USE_MOCK_SERVICES:
        return mock_check_payments(user_id)

    url = USER_CASHBACKS.format(str(user_id))
    try:
        response = requests.get(url=url, headers=headers1)

    except:
        raise ConnectionError(f"Cashback service not responding in {check_payments.__name__}")

    if response.status_code == 200:
        data = response.json()

        return [
            {
                "date": item.get("date"),
                "sum": item.get("sum"),
                "coin": item.get("coin"),
            }
            for item in data.get("cashbackList", [])
        ]

    else:
        raise ConnectionError(f"Cashback service {check_payments.__name__} doesn't work. status_code is: {response.status_code}")


def check_payouts(user_id: str):
    # список снятий кэшбэка с датой и суммой
    if USE_MOCK_SERVICES:
        return mock_check_payouts(user_id)

    url = USER_PAYOUTS.format(str(user_id))
    try:
        response = requests.get(url=url, headers=headers1)

    except:
        raise ConnectionError(f"Cashback service not responding in {check_payouts.__name__}")

    if response.status_code == 200:
        data = response.json()

        return [
            {
                "acceptedAt": item.get("acceptedAt"),
                "sum": item.get("sum"),
                "type": item.get("type"),
                "status": item.get("status"),
                "currency" : item.get("currency"),
            }
            for item in data
        ]

    else:
        raise ConnectionError(f"Cashback service {check_payouts.__name__} doesn't work. status_code is: {response.status_code}")

