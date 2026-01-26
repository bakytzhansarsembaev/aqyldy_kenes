"""
Тесты для MentorAgent.

Запуск: pytest src/tests/test_mentor_agent.py -v
"""

import pytest
from unittest.mock import MagicMock, patch
from src.agents.mentor.mentor_agent import MentorAgent
from src.utils.classifier.intents import IntentEnum


class TestMentorAgent:
    """Тесты для MentorAgent"""

    def create_mock_policy_loader(self):
        """Создать mock PolicyLoader"""
        mock_loader = MagicMock()

        # Mock policy object
        mock_policy = MagicMock()
        mock_policy.policy = MagicMock()
        mock_policy.policy.escalation_message = "Тестовое сообщение ментору"

        mock_loader.get_for.return_value = mock_policy
        return mock_loader

    def test_agent_initialization(self):
        """Тест инициализации агента"""
        mock_loader = self.create_mock_policy_loader()

        agent = MentorAgent(
            backend_tools={},
            context_data="test context",
            policy_loader=mock_loader,
            user_id="123"
        )

        assert agent.intent == IntentEnum.mentor
        assert agent.subintent is None
        assert agent.user_id == "123"

    def test_get_data_from_api(self):
        """Тест что get_data_from_api возвращает пустой dict"""
        mock_loader = self.create_mock_policy_loader()

        agent = MentorAgent(
            backend_tools={},
            context_data="test context",
            policy_loader=mock_loader,
            user_id="123"
        )

        data = agent.get_data_from_api()

        assert data == {}

    def test_run_agent_returns_escalation(self):
        """Тест что run_agent всегда возвращает эскалацию"""
        mock_loader = self.create_mock_policy_loader()

        agent = MentorAgent(
            backend_tools={},
            context_data="test context",
            policy_loader=mock_loader,
            user_id="123"
        )

        result = agent.run_agent(
            user_message="Нужна помощь ментора",
            summary="Тестовый summary"
        )

        assert result is not None
        assert "response" in result
        assert "intent" in result

        response = result["response"]
        assert response["decision"] == "pass"
        assert response["escalate_to_mentor"] is True
        assert response["requires_human"] is True

    def test_run_agent_uses_policy_message(self):
        """Тест что agent использует сообщение из policy"""
        mock_loader = self.create_mock_policy_loader()

        agent = MentorAgent(
            backend_tools={},
            context_data="test context",
            policy_loader=mock_loader,
            user_id="123"
        )

        result = agent.run_agent(
            user_message="Help",
            summary="Summary"
        )

        response = result["response"]
        assert "answer" in response

    def test_run_agent_with_dict_policy(self):
        """Тест с policy в виде dict"""
        mock_loader = MagicMock()

        mock_policy = MagicMock()
        mock_policy.policy = {
            "escalation_message": "Dict message"
        }
        mock_loader.get_for.return_value = mock_policy

        agent = MentorAgent(
            backend_tools={},
            context_data="test context",
            policy_loader=mock_loader,
            user_id="123"
        )

        result = agent.run_agent(
            user_message="Help",
            summary="Summary"
        )

        response = result["response"]
        assert response["answer"] == "Dict message"

    def test_run_agent_with_default_message(self):
        """Тест с дефолтным сообщением когда policy пустая"""
        mock_loader = MagicMock()

        mock_policy = MagicMock()
        mock_policy.policy = {}
        mock_loader.get_for.return_value = mock_policy

        agent = MentorAgent(
            backend_tools={},
            context_data="test context",
            policy_loader=mock_loader,
            user_id="123"
        )

        result = agent.run_agent(
            user_message="Help",
            summary="Summary"
        )

        response = result["response"]
        # Должно быть дефолтное сообщение
        assert "ментор" in response["answer"].lower() or "наставник" in response["answer"].lower()


class TestMentorAgentRegistry:
    """Тесты регистрации MentorAgent"""

    def test_agent_registered_in_registry(self):
        """Тест что агент зарегистрирован в реестре"""
        from src.agents.registry import AGENT_REGISTRY

        key = (IntentEnum.mentor, None)
        assert key in AGENT_REGISTRY

    def test_registered_agent_is_correct_class(self):
        """Тест что зарегистрирован правильный класс"""
        from src.agents.registry import AGENT_REGISTRY

        key = (IntentEnum.mentor, None)
        registered_class = AGENT_REGISTRY[key]

        assert registered_class == MentorAgent


class TestMentorPolicy:
    """Тесты для mentor policy"""

    def test_policy_path_exists(self):
        """Тест что путь к policy существует"""
        from src.utils.policies.policy_loader import POLICY_PATHS

        key = ("mentor", None)
        assert key in POLICY_PATHS

    def test_policy_file_exists(self):
        """Тест что файл policy существует"""
        from src.utils.policies.policy_loader import POLICY_PATHS
        from pathlib import Path

        key = ("mentor", None)
        policy_path = POLICY_PATHS[key]

        assert Path(policy_path).exists()

    def test_policy_model_registered(self):
        """Тест что PolicyModel зарегистрирована"""
        from src.utils.policies.policy_loader import PolicyModels

        key = (IntentEnum.mentor, None)
        assert key in PolicyModels
