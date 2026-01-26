"""
Mock-сервисы для тестирования без реального API
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List


# === MOCK DATA ===

MOCK_USER = {
    "user_id": "test_user_123",
    "login": "+7-777-123-45-67",
    "password": "qwerty123",
    "name": "Тестовый Ученик",
    "grade": 7
}

MOCK_CASHBACK = {
    "cashback_sum": 15000,  # тенге
    "cashback_list": [
        {"date": "2025-01-15", "sum": 5000, "coin": "KZT"},
        {"date": "2025-01-10", "sum": 5000, "coin": "KZT"},
        {"date": "2025-01-05", "sum": 5000, "coin": "KZT"},
    ],
    "payout_list": [
        {"acceptedAt": "2025-01-12", "sum": 3000, "type": "withdrawal", "status": "completed", "currency": "KZT"},
    ]
}

MOCK_FREEZINGS = {
    "active": [
        {"date": (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d")},
    ],
    "past": [
        {"date": "2025-01-10"},
        {"date": "2025-01-05"},
    ],
    "total_available": 5,
    "used": 2
}

MOCK_TASK = {
    "task_id": "task_12345",
    "task_text": "Решите уравнение: 2x + 5 = 15",
    "task_type": "personal_study",
    "subject": "Математика",
    "grade": 7,
    "has_subscription": True,
    "personal_study_completed": False
}


# === MOCK FUNCTIONS ===

# Cashback mock functions
def mock_cashback_sum(user_id: str) -> Dict[str, int]:
    return {"cashback_sum": MOCK_CASHBACK["cashback_sum"]}


def mock_check_users_password(user_id: str) -> Dict[str, str]:
    return {"login": MOCK_USER["login"], "password": MOCK_USER["password"]}


def mock_check_payments(user_id: str) -> List[Dict]:
    return MOCK_CASHBACK["cashback_list"]


def mock_check_payouts(user_id: str) -> List[Dict]:
    return MOCK_CASHBACK["payout_list"]


# Freezing mock functions
def mock_check_freezings(user_id: str) -> List[Dict]:
    return MOCK_FREEZINGS["active"] + MOCK_FREEZINGS["past"]


def mock_check_active_freezings(user_id: str) -> List[Dict]:
    return MOCK_FREEZINGS["active"]


def mock_check_past_freezings(user_id: str) -> List[Dict]:
    return MOCK_FREEZINGS["past"]


# Task mock functions
def mock_get_current_task(user_id: str) -> Optional[Dict[str, Any]]:
    return MOCK_TASK
