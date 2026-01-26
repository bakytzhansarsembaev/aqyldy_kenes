from datetime import datetime, date

import requests, json
from src.configs.settings import headers1, USER_FREEZINGS, USE_MOCK_SERVICES

if USE_MOCK_SERVICES:
    from src.tools.services.mock_services import (
        mock_check_freezings, mock_check_active_freezings, mock_check_past_freezings
    )


def check_freezings(user_id: str):
    # список дат заморозок
    if USE_MOCK_SERVICES:
        return mock_check_freezings(user_id)

    url = USER_FREEZINGS.format(str(user_id))
    try:
        response = requests.get(url=url, headers=headers1)

    except:
        raise ConnectionError(f"Cashback service not responding in {check_freezings.__name__}")

    if response.status_code == 200:
        data = response.json()

        return [
            {
                "date": item.get("date"),
            }
            for item in data.get("freezings", [])
        ]


    else:
        raise ConnectionError(
            f"Cashback service {check_freezings.__name__} doesn't work. status_code is: {response.status_code}")


def check_active_freezings(user_id: str):
    # список дат активных заморозок
    if USE_MOCK_SERVICES:
        return mock_check_active_freezings(user_id)

    url = USER_FREEZINGS.format(str(user_id))
    try:
        response = requests.get(url=url, headers=headers1)

    except:
        raise ConnectionError(f"Cashback service not responding in {check_active_freezings.__name__}")

    if response.status_code == 200:
        data = response.json()

        return [
            {
                "date": item.get("date"),
            }
            for item in data.get("freezings", [])
            if item.get("date") and datetime.fromisoformat(item["date"]).date() > date.today()
        ]

    else:
        raise ConnectionError(
            f"Cashback service {check_active_freezings.__name__} doesn't work. status_code is: {response.status_code}")


def check_past_freezings(user_id: str):
    # список дат ранее поставленных заморозок заморозок
    if USE_MOCK_SERVICES:
        return mock_check_past_freezings(user_id)

    url = USER_FREEZINGS.format(str(user_id))
    try:
        response = requests.get(url=url, headers=headers1)

    except:
        raise ConnectionError(f"Cashback service not responding in {check_past_freezings.__name__}")

    if response.status_code == 200:
        data = response.json()

        return [
            {
                "date": item.get("date"),
            }
            for item in data.get("freezings", [])
            if item.get("date") and datetime.fromisoformat(item["date"]).date() <= date.today()
        ]


    else:
        raise ConnectionError(
            f"Cashback service {check_past_freezings.__name__} doesn't work. status_code is: {response.status_code}")

