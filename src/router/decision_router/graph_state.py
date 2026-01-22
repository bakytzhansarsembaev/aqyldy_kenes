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

    # маршрутизация
    selected_agent: Optional[str] = None

    # последний использовавшийся агент
    last_agent: Optional[str] = None

    # ответ агента
    agent_answer: Optional[str] = None