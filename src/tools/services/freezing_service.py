from datetime import datetime, date
from typing import List

import requests, json
from src.configs.settings import headers1, USER_FREEZINGS, USE_MOCK_FREEZING, USABLE_BRANCH

if USE_MOCK_FREEZING:
    from src.tools.services.mock_services import (
        mock_check_freezings, mock_check_active_freezings, mock_check_past_freezings
    )

# TODO: Добавить правильный endpoint когда будет известен
SET_FREEZING_URL = USABLE_BRANCH + '/api/users/{}/freezings'


def set_freezing(user_id: str, dates: List[str]) -> dict:
    """
    Устанавливает заморозку на указанные даты.

    Args:
        user_id: ID пользователя
        dates: Список дат в формате "YYYY-MM-DD"

    Returns:
        dict с результатом: {"success": True/False, "message": "..."}
    """
    # TODO: Раскомментировать когда API endpoint будет готов
    # url = SET_FREEZING_URL.format(str(user_id))
    # try:
    #     response = requests.post(
    #         url=url,
    #         headers=headers1,
    #         json={"dates": dates}
    #     )
    #     if response.status_code == 200:
    #         return {"success": True, "message": f"Заморозка установлена на: {', '.join(dates)}"}
    #     else:
    #         return {"success": False, "message": f"Ошибка API: {response.status_code}"}
    # except Exception as e:
    #     return {"success": False, "message": f"Ошибка соединения: {str(e)}"}

    # Пока возвращаем успех без реального API вызова
    print(f"[FREEZING] Would set freezing for user_id={user_id} on dates: {dates}")
    return {"success": True, "message": f"Заморозка қойылды: {', '.join(dates)}", "dates": dates}


def check_freezings(user_id: str):
    # список дат заморозок
    if USE_MOCK_FREEZING:
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
    if USE_MOCK_FREEZING:
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
    if USE_MOCK_FREEZING:
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

