import requests
import json
from src.configs.settings import USER_CURRENT_TASK, headers1, USE_MOCK_SERVICES
from typing import Optional, Dict, Any


def mock_get_current_task(user_id: str) -> Optional[Dict[str, Any]]:
    """
    Mock данные для тестирования (используется когда USE_MOCK_SERVICES=true)
    """
    return {
        "task_id": "mock_12345",
        "task_text": "Решите уравнение: 2x + 5 = 15",
        "task_type": "personal_study",
        "subject": "Математика",
        "grade": 7,
        "has_subscription": True,
        "personal_study_completed": False
    }


def get_current_task(user_id: str) -> Optional[Dict[str, Any]]:
    """
    Получить информацию о текущей задаче ученика.

    В тестовом режиме (USE_MOCK_SERVICES=true) возвращает mock данные.
    В production (USE_MOCK_SERVICES=false) делает реальный API запрос.

    Args:
        user_id: ID пользователя

    Returns:
        Dict с данными задачи:
        {
            "task_id": str,
            "task_text": str,
            "task_type": str,  # "personal_study" | "diagnostics" | "math"
            "subject": str,
            "grade": int,
            "has_subscription": bool,
            "personal_study_completed": bool
        }
        Или None при ошибке
    """

    # ============================================
    # MOCK режим для тестирования
    # ============================================
    if USE_MOCK_SERVICES:
        print(f"[MOCK] get_current_task for user_id={user_id}")
        return mock_get_current_task(user_id)

    # ============================================
    # PRODUCTION режим - реальный API
    # ============================================
    url = USER_CURRENT_TASK.format(user_id)

    try:
        response = requests.get(url=url, headers=headers1, timeout=5)

        if response.status_code == 200:
            data = response.json()

            # Маппинг API response -> наш формат
            result = {
                "task_id": data.get("taskId") or data.get("task_id"),
                "task_text": data.get("taskText") or data.get("task_text"),
                "task_type": data.get("taskType") or data.get("task_type", "personal_study"),
                "subject": data.get("subject") or data.get("subjectName"),
                "grade": data.get("grade") or data.get("gradeNumber"),
                "has_subscription": data.get("hasSubscription", True),
                "personal_study_completed": data.get("personalStudyCompleted", False)
            }

            print(f"[API] Successfully fetched task for user_id={user_id}")
            return result

        elif response.status_code == 404:
            print(f"[API] No current task for user_id={user_id}")
            return None

        else:
            print(f"[API ERROR] Status {response.status_code} for user_id={user_id}")
            return None

    except requests.Timeout:
        print(f"[API ERROR] Timeout for user_id={user_id}")
        return None

    except requests.RequestException as e:
        print(f"[API ERROR] Connection error for user_id={user_id}: {e}")
        return None

    except json.JSONDecodeError as e:
        print(f"[API ERROR] JSON decode error for user_id={user_id}: {e}")
        return None

    except Exception as e:
        print(f"[API ERROR] Unexpected error for user_id={user_id}: {e}")
        return None


def get_task_section(user_id: str) -> Optional[Dict[str, Any]]:
    """
    Получить информацию о разделе задач пользователя (personal study).

    Args:
        user_id: ID пользователя

    Returns:
        Dict с данными раздела или None при ошибке
    """
    from src.configs.settings import USER_TASK_SECTION

    if USE_MOCK_SERVICES:
        print(f"[MOCK] get_task_section for user_id={user_id}")
        return {
            "section_id": "mock_section",
            "total_tasks": 10,
            "completed_tasks": 3,
            "current_task_index": 4
        }

    url = USER_TASK_SECTION.format(user_id)

    try:
        response = requests.get(url=url, headers=headers1, timeout=5)

        if response.status_code == 200:
            data = response.json()
            print(f"[API] Successfully fetched task section for user_id={user_id}")
            return data
        else:
            print(f"[API ERROR] Status {response.status_code} for task section, user_id={user_id}")
            return None

    except requests.Timeout:
        print(f"[API ERROR] Timeout for task section, user_id={user_id}")
        return None

    except requests.RequestException as e:
        print(f"[API ERROR] Connection error for task section, user_id={user_id}: {e}")
        return None

    except Exception as e:
        print(f"[API ERROR] Unexpected error for task section, user_id={user_id}: {e}")
        return None


def get_daily_personal_study(user_id: str) -> Optional[Dict[str, Any]]:
    """
    Получить информацию о дневном личном обучении.

    Args:
        user_id: ID пользователя

    Returns:
        Dict с данными дневного обучения или None при ошибке
    """
    from src.configs.settings import USER_DAILY_PERSONAL_STUDY

    if USE_MOCK_SERVICES:
        print(f"[MOCK] get_daily_personal_study for user_id={user_id}")
        return {
            "daily_goal": 5,
            "completed_today": 2,
            "streak_days": 7
        }

    url = USER_DAILY_PERSONAL_STUDY.format(user_id)

    try:
        response = requests.get(url=url, headers=headers1, timeout=5)

        if response.status_code == 200:
            data = response.json()
            print(f"[API] Successfully fetched daily personal study for user_id={user_id}")
            return data
        else:
            print(f"[API ERROR] Status {response.status_code} for daily study, user_id={user_id}")
            return None

    except requests.Timeout:
        print(f"[API ERROR] Timeout for daily study, user_id={user_id}")
        return None

    except requests.RequestException as e:
        print(f"[API ERROR] Connection error for daily study, user_id={user_id}: {e}")
        return None

    except Exception as e:
        print(f"[API ERROR] Unexpected error for daily study, user_id={user_id}: {e}")
        return None
