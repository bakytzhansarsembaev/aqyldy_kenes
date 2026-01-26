import requests
import json
from src.configs.settings import USER_CURRENT_TASK, headers1, USE_MOCK_SERVICES
from typing import Optional, Dict, Any

if USE_MOCK_SERVICES:
    from src.tools.services.mock_services import mock_get_current_task


def get_current_task(user_id: str) -> Optional[Dict[str, Any]]:
    """
    Получить информацию о текущей задаче ученика
    
    Args:
        user_id: ID пользователя
        
    Returns:
        Dict с данными задачи или None при ошибке
        {
            "task_id": str,
            "task_text": str,
            "task_type": str,  # "personal_study" | "diagnostics" | "math"
            "subject": str,
            "grade": int,
            "has_subscription": bool,
            "personal_study_completed": bool
        }
    """
    if USE_MOCK_SERVICES:
        return mock_get_current_task(user_id)

    url = USER_CURRENT_TASK.format(user_id)
    
    try:
        response = requests.get(url=url, headers=headers1)
        
        if response.status_code == 200:
            data = response.json()
            
            return {
                "task_id": data.get("taskId"),
                "task_text": data.get("taskText"),
                "task_type": data.get("taskType", "personal_study"),
                "subject": data.get("subject"),
                "grade": data.get("grade"),
                "has_subscription": data.get("hasSubscription", True),
                "personal_study_completed": data.get("personalStudyCompleted", False)
            }
        
        else:
            print(f"Task service error: status_code {response.status_code}")
            return None
            
    except requests.RequestException as e:
        print(f"Task service connection error: {e}")
        return None
        
    except Exception as e:
        print(f"Task service unexpected error: {e}")
        return None