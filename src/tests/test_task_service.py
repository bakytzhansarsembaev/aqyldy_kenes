"""
Тесты для Task Service.

Запуск: pytest src/tests/test_task_service.py -v
"""

import pytest
from unittest.mock import patch, MagicMock
from src.tools.services.task_service import (
    get_current_task,
    get_task_section,
    get_daily_personal_study,
    mock_get_current_task
)


class TestMockMode:
    """Тесты mock режима"""

    @patch('src.tools.services.task_service.USE_MOCK_SERVICES', True)
    def test_mock_get_current_task(self):
        """Тест mock режима для get_current_task"""
        task = get_current_task("123")

        assert task is not None
        assert task["task_id"] == "mock_12345"
        assert task["task_type"] == "personal_study"
        assert task["subject"] == "Математика"
        assert task["grade"] == 7
        assert task["has_subscription"] is True

    def test_mock_data_structure(self):
        """Тест структуры mock данных"""
        task = mock_get_current_task("any_id")

        required_fields = [
            "task_id", "task_text", "task_type",
            "subject", "grade", "has_subscription",
            "personal_study_completed"
        ]

        for field in required_fields:
            assert field in task, f"Missing field: {field}"

    @patch('src.tools.services.task_service.USE_MOCK_SERVICES', True)
    def test_mock_get_task_section(self):
        """Тест mock режима для get_task_section"""
        section = get_task_section("123")

        assert section is not None
        assert "section_id" in section
        assert "total_tasks" in section

    @patch('src.tools.services.task_service.USE_MOCK_SERVICES', True)
    def test_mock_get_daily_personal_study(self):
        """Тест mock режима для get_daily_personal_study"""
        daily = get_daily_personal_study("123")

        assert daily is not None
        assert "daily_goal" in daily
        assert "completed_today" in daily


class TestProductionMode:
    """Тесты production режима (с мокированием requests)"""

    @patch('src.tools.services.task_service.USE_MOCK_SERVICES', False)
    @patch('src.tools.services.task_service.requests.get')
    def test_successful_api_call(self, mock_get):
        """Тест успешного API вызова"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "taskId": "api_123",
            "taskText": "Solve: 2+2",
            "taskType": "personal_study",
            "subject": "Math",
            "grade": 5,
            "hasSubscription": True,
            "personalStudyCompleted": False
        }
        mock_get.return_value = mock_response

        task = get_current_task("123")

        assert task is not None
        assert task["task_id"] == "api_123"
        assert task["task_text"] == "Solve: 2+2"
        assert task["task_type"] == "personal_study"

    @patch('src.tools.services.task_service.USE_MOCK_SERVICES', False)
    @patch('src.tools.services.task_service.requests.get')
    def test_api_404_response(self, mock_get):
        """Тест 404 ответа API"""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        task = get_current_task("123")

        assert task is None

    @patch('src.tools.services.task_service.USE_MOCK_SERVICES', False)
    @patch('src.tools.services.task_service.requests.get')
    def test_api_500_response(self, mock_get):
        """Тест 500 ответа API"""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_get.return_value = mock_response

        task = get_current_task("123")

        assert task is None

    @patch('src.tools.services.task_service.USE_MOCK_SERVICES', False)
    @patch('src.tools.services.task_service.requests.get')
    def test_api_timeout(self, mock_get):
        """Тест timeout API"""
        import requests
        mock_get.side_effect = requests.Timeout()

        task = get_current_task("123")

        assert task is None

    @patch('src.tools.services.task_service.USE_MOCK_SERVICES', False)
    @patch('src.tools.services.task_service.requests.get')
    def test_api_connection_error(self, mock_get):
        """Тест ошибки соединения"""
        import requests
        mock_get.side_effect = requests.ConnectionError()

        task = get_current_task("123")

        assert task is None

    @patch('src.tools.services.task_service.USE_MOCK_SERVICES', False)
    @patch('src.tools.services.task_service.requests.get')
    def test_api_json_decode_error(self, mock_get):
        """Тест ошибки парсинга JSON"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_get.return_value = mock_response

        task = get_current_task("123")

        assert task is None


class TestFieldMapping:
    """Тесты маппинга полей API"""

    @patch('src.tools.services.task_service.USE_MOCK_SERVICES', False)
    @patch('src.tools.services.task_service.requests.get')
    def test_camel_case_mapping(self, mock_get):
        """Тест маппинга camelCase полей"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "taskId": "123",
            "taskText": "Test",
            "taskType": "math",
            "subjectName": "Algebra",
            "gradeNumber": 8,
            "hasSubscription": False
        }
        mock_get.return_value = mock_response

        task = get_current_task("123")

        assert task["task_id"] == "123"
        assert task["task_text"] == "Test"
        assert task["subject"] == "Algebra"
        assert task["grade"] == 8

    @patch('src.tools.services.task_service.USE_MOCK_SERVICES', False)
    @patch('src.tools.services.task_service.requests.get')
    def test_snake_case_mapping(self, mock_get):
        """Тест маппинга snake_case полей"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "task_id": "456",
            "task_text": "Test2",
            "task_type": "diagnostics"
        }
        mock_get.return_value = mock_response

        task = get_current_task("123")

        assert task["task_id"] == "456"
        assert task["task_text"] == "Test2"
        assert task["task_type"] == "diagnostics"


class TestEdgeCases:
    """Тесты граничных случаев"""

    @patch('src.tools.services.task_service.USE_MOCK_SERVICES', False)
    @patch('src.tools.services.task_service.requests.get')
    def test_empty_response(self, mock_get):
        """Тест пустого ответа"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {}
        mock_get.return_value = mock_response

        task = get_current_task("123")

        assert task is not None
        assert task["task_id"] is None

    @patch('src.tools.services.task_service.USE_MOCK_SERVICES', False)
    @patch('src.tools.services.task_service.requests.get')
    def test_partial_response(self, mock_get):
        """Тест частичного ответа"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "taskId": "789"
            # Остальные поля отсутствуют
        }
        mock_get.return_value = mock_response

        task = get_current_task("123")

        assert task is not None
        assert task["task_id"] == "789"
        assert task["task_type"] == "personal_study"  # Default value
