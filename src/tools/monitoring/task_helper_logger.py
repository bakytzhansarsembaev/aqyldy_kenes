"""
Task Helper Logger - централизованное логирование событий Task Helper.

Записывает события в logs/task_helper.log в JSON формате для удобного анализа.
"""

import logging
import json
import os
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path


# Создаём директорию для логов если её нет
LOG_DIR = Path(__file__).parent.parent.parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

# Настройка логгера
logger = logging.getLogger("TaskHelper")
logger.setLevel(logging.INFO)

# Проверяем, не добавлен ли уже handler
if not logger.handlers:
    # Файловый handler
    log_file = LOG_DIR / "task_helper.log"
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.INFO)

    # Формат логов
    formatter = logging.Formatter(
        '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Console handler для отладки
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)


class TaskHelperEvent:
    """Типы событий Task Helper"""
    TASK_FETCHED = "task_fetched"
    HINT_GIVEN = "hint_given"
    ESCALATION = "escalation"
    TASK_COMPLETED = "task_completed"
    API_ERROR = "api_error"
    LATEX_PROCESSED = "latex_processed"
    VALIDATION_ERROR = "validation_error"
    SESSION_START = "session_start"
    SESSION_END = "session_end"
    AGENT_INVOKED = "agent_invoked"


def log_event(
    user_id: str,
    event_type: str,
    details: Optional[Dict[str, Any]] = None,
    level: str = "INFO"
):
    """
    Централизованное логирование событий Task Helper

    Args:
        user_id: ID пользователя
        event_type: Тип события (из TaskHelperEvent)
        details: Дополнительные данные
        level: Уровень лога (INFO/WARNING/ERROR)
    """
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "user_id": str(user_id),
        "event": event_type,
        "details": details or {}
    }

    log_message = json.dumps(log_entry, ensure_ascii=False)

    if level == "ERROR":
        logger.error(log_message)
    elif level == "WARNING":
        logger.warning(log_message)
    else:
        logger.info(log_message)


def log_task_fetched(user_id: str, task_data: Dict[str, Any]):
    """Логирование успешного получения задачи"""
    log_event(
        user_id=user_id,
        event_type=TaskHelperEvent.TASK_FETCHED,
        details={
            "task_id": task_data.get("task_id"),
            "task_type": task_data.get("task_type"),
            "subject": task_data.get("subject"),
            "has_task_text": bool(task_data.get("task_text"))
        }
    )


def log_hint_given(user_id: str, hint_level: int, task_id: Optional[str] = None):
    """Логирование выдачи подсказки"""
    log_event(
        user_id=user_id,
        event_type=TaskHelperEvent.HINT_GIVEN,
        details={
            "hint_level": hint_level,
            "task_id": task_id
        }
    )


def log_escalation(user_id: str, reason: str, hints_given: int):
    """Логирование эскалации к ментору"""
    log_event(
        user_id=user_id,
        event_type=TaskHelperEvent.ESCALATION,
        details={
            "reason": reason,
            "hints_given": hints_given
        },
        level="WARNING"
    )


def log_task_completed(user_id: str, task_id: str, hints_used: int):
    """Логирование успешного решения задачи"""
    log_event(
        user_id=user_id,
        event_type=TaskHelperEvent.TASK_COMPLETED,
        details={
            "task_id": task_id,
            "hints_used": hints_used,
            "success": True
        }
    )


def log_api_error(user_id: str, error_type: str, error_message: str):
    """Логирование ошибок API"""
    log_event(
        user_id=user_id,
        event_type=TaskHelperEvent.API_ERROR,
        details={
            "error_type": error_type,
            "error_message": error_message
        },
        level="ERROR"
    )


def log_latex_processed(user_id: str, formulas_count: int):
    """Логирование обработки LaTeX"""
    log_event(
        user_id=user_id,
        event_type=TaskHelperEvent.LATEX_PROCESSED,
        details={
            "formulas_count": formulas_count
        }
    )


def log_session_start(user_id: str, task_id: Optional[str] = None):
    """Логирование начала сессии Task Helper"""
    log_event(
        user_id=user_id,
        event_type=TaskHelperEvent.SESSION_START,
        details={
            "task_id": task_id
        }
    )


def log_session_end(user_id: str, total_hints: int, completed: bool):
    """Логирование завершения сессии Task Helper"""
    log_event(
        user_id=user_id,
        event_type=TaskHelperEvent.SESSION_END,
        details={
            "total_hints": total_hints,
            "completed": completed
        }
    )


def log_agent_invoked(user_id: str, agent_type: str, subintent: Optional[str] = None):
    """Логирование вызова агента"""
    log_event(
        user_id=user_id,
        event_type=TaskHelperEvent.AGENT_INVOKED,
        details={
            "agent_type": agent_type,
            "subintent": subintent
        }
    )


def log_validation_error(user_id: str, field: str, error_message: str):
    """Логирование ошибок валидации"""
    log_event(
        user_id=user_id,
        event_type=TaskHelperEvent.VALIDATION_ERROR,
        details={
            "field": field,
            "error_message": error_message
        },
        level="WARNING"
    )


# ============================================
# Утилиты для анализа логов
# ============================================

def get_recent_logs(lines: int = 100) -> list:
    """
    Получить последние N строк из лога.

    Args:
        lines: Количество строк

    Returns:
        Список словарей с событиями
    """
    log_file = LOG_DIR / "task_helper.log"
    if not log_file.exists():
        return []

    events = []
    with open(log_file, 'r', encoding='utf-8') as f:
        all_lines = f.readlines()
        for line in all_lines[-lines:]:
            try:
                # Извлекаем JSON из строки лога
                if '{' in line:
                    json_start = line.index('{')
                    json_str = line[json_start:]
                    events.append(json.loads(json_str))
            except (json.JSONDecodeError, ValueError):
                continue

    return events


def get_user_events(user_id: str, limit: int = 50) -> list:
    """
    Получить события для конкретного пользователя.

    Args:
        user_id: ID пользователя
        limit: Максимальное количество событий

    Returns:
        Список событий пользователя
    """
    all_events = get_recent_logs(lines=1000)
    user_events = [e for e in all_events if e.get("user_id") == str(user_id)]
    return user_events[-limit:]


def count_events_by_type(hours: int = 24) -> Dict[str, int]:
    """
    Подсчитать события по типам за последние N часов.

    Args:
        hours: Количество часов

    Returns:
        Словарь {event_type: count}
    """
    from datetime import timedelta

    events = get_recent_logs(lines=10000)
    cutoff = datetime.now() - timedelta(hours=hours)

    counts = {}
    for event in events:
        try:
            event_time = datetime.fromisoformat(event.get("timestamp", ""))
            if event_time >= cutoff:
                event_type = event.get("event", "unknown")
                counts[event_type] = counts.get(event_type, 0) + 1
        except ValueError:
            continue

    return counts
