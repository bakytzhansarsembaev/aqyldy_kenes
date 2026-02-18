from pydantic import BaseModel
from typing import Dict, Any, Optional, List


# пропишем первичный graph_state скелет, впоследствии будем его расширять
class BotState(BaseModel):
    user_id: str
    user_message: str

    # контекст
    summary: Optional[str] = None
    previous_intent: Optional[str] = None
    previous_subintent: Optional[str] = None
    # previous_summary: Optional[str] = None
    usable_context: Optional[List[Dict]] = None

    # результат классификации
    intent: Optional[str] = None
    subintent: Optional[str] = None
    shift: bool = False # позже добавлю смену intent при повторной классификации
    confidence_score: Optional[float] = None

    # Task Helper

    # маршрутизация
    selected_agent: Optional[str] = None

    # последний использовавшийся агент
    last_agent: Optional[str] = None

    # ответ агента (dict с ключами: response, intent, subintent)
    agent_answer: Optional[Dict[str, Any]] = None

    # Флаг активной сессии с Task Helper
    task_helper_active: bool = False

    # Текущий уровень подсказки (1-5)
    current_hint_level: int = 0

    # Текст задачи из API (для контекста)
    task_context: Optional[Dict[str, Any]] = None  # {"task_text": "...", "task_type": "..."}

    # Количество подсказок, уже данных в текущей сессии
    hints_given: int = 0

    # Флаг эскалации к ментору
    escalate_to_mentor: bool = False

    # Session management
    task_confirmed: bool = False           # Задача подтверждена учеником
    confirmed_task_id: Optional[str] = None  # ID подтверждённой задачи
    session_start_time: Optional[str] = None  # Время начала сеанса (ISO format)
    last_message_time: Optional[str] = None   # Время последнего сообщения
    session_closed: bool = False           # Флаг закрытия сессии
    close_reason: Optional[str] = None     # Причина закрытия