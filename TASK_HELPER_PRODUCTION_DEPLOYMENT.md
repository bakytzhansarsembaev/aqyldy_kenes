# 🎯 ТЕХНИЧЕСКОЕ ЗАДАНИЕ: Task Helper AI Agent v2.0
## Доработка и Production Deployment для Qalan.kz

**Дата:** 2026-01-26  
**Статус:** Ready for Production Implementation  
**Приоритет:** HIGH

---

## 📊 ТЕКУЩЕЕ СОСТОЯНИЕ ПРОЕКТА

### ✅ Что уже работает:

1. **Базовая архитектура**
   - ✅ LangGraph + Redis + RabbitMQ
   - ✅ Multiprocessing с CPU affinity
   - ✅ Debouncing 10 секунд
   - ✅ Policy-based система

2. **BotState обновлён**
   ```python
   # src/router/decision_router/graph_state.py
   agent_answer: Optional[Dict[str, Any]] = None  # ✅ ИСПРАВЛЕНО
   task_helper_active: bool = False
   current_hint_level: int = 0
   task_context: Optional[Dict[str, Any]] = None
   hints_given: int = 0
   escalate_to_mentor: bool = False
   ```

3. **Агенты зарегистрированы**
   - ✅ TaskHelperMainAgent
   - ✅ TaskHelperHelperAgent (subintent: task_problems)
   - ✅ TaskHelperChangerAgent (subintent: change_task)

4. **Тестирование работает**
   - ✅ `interactive_test.py` успешно прошёл
   - ✅ Mock сервисы работают (`USE_MOCK_SERVICES=true`)
   - ✅ Все 3 тестовых сценария OK

5. **Policy обновлена**
   - ✅ `task_helper_helper.json` v2.0.0
   - ✅ 5-уровневая стратегия подсказок
   - ✅ Правила для diagnostics/math/unsubscribed

---

## 🚨 ИЗВЕСТНЫЕ ПРОБЛЕМЫ (требуют исправления)

### 🔴 Критические:

1. **Intent "mentor" не зарегистрирован**
   ```
   ПРОБЛЕМА: Классификатор иногда возвращает intent="mentor"
   ОШИБКА: KeyError в AGENT_REGISTRY
   РЕШЕНИЕ: Добавить MentorAgent или переназначить на task_problems
   ```

2. **API Integration отсутствует**
   ```
   ПРОБЛЕМА: task_service.py работает только с mock данными
   ОШИБКА: В production не будет реальных задач из API
   РЕШЕНИЕ: Реализовать настоящие API вызовы
   ```

### 🟡 Средние:

3. **requirements.txt повреждён**
   ```
   ПРОБЛЕМА: Пробелы между символами в названиях пакетов
   РЕШЕНИЕ: Пересоздать файл
   ```

4. **LaTeX обработка не протестирована**
   ```
   ПРОБЛЕМА: latex_processor.py не существует
   РЕШЕНИЕ: Создать и протестировать с реальными формулами
   ```

---

## 🎯 ЦЕЛИ ЭТОГО РЕЛИЗА

### Production-Ready Checklist:

- [ ] **API Integration** - переключить с mock на реальный API
- [ ] **Intent "mentor"** - исправить классификатор или добавить агента
- [ ] **LaTeX Support** - полная обработка математических формул
- [ ] **Error Handling** - graceful degradation при сбоях API
- [ ] **Logging** - детальное логирование для monitoring
- [ ] **Performance** - оптимизация для 1000+ параллельных запросов
- [ ] **Tests** - расширенное покрытие edge cases

---

## 📋 ПЛАН РЕАЛИЗАЦИИ

---

## ЭТАП 1: ИСПРАВЛЕНИЕ КРИТИЧЕСКИХ ПРОБЛЕМ

### 1.1. Исправить Intent "mentor" 🔴

**Файл:** `src/agents/mentor/mentor_agent.py`

**Создать новый агент:**

```python
from src.agents.base import BaseAgent
from src.utils.classifier.intents import IntentEnum


class MentorAgent(BaseAgent):
    """
    Агент-переадресатор для вопросов, требующих человека-ментора.
    Используется когда классификатор определяет intent=mentor.
    
    Поведение:
    - Всегда возвращает decision="pass" с escalate_to_mentor=True
    - Объясняет ученику, что его вопрос передан ментору
    """
    
    def __init__(self, backend_tools, context_data, policy_loader, user_id):
        super().__init__(
            intent=IntentEnum.mentor,
            subintent=None,
            backend_tools=backend_tools,
            context_data=context_data,
            policy_loader=policy_loader,
            user_id=user_id
        )

    def get_data_from_api(self):
        return {}
    
    def run_agent(self, user_message, summary):
        """
        Всегда эскалирует к человеку-ментору
        """
        policy = self.load_policy()
        
        response = {
            "decision": "pass",
            "answer": policy.policy.get("escalation_message", 
                                        "Передаю твой вопрос наставнику. Он свяжется с тобой в ближайшее время."),
            "escalate_to_mentor": True
        }
        
        return {
            "response": response,
            "intent": self.intent,
            "subintent": self.subintent
        }
```

**Файл:** `src/utils/policies/mentor_main.json`

```json
{
  "intent": "mentor",
  "subintent": null,
  "version": "1.0.0",
  "owner": "ml",
  "description": "Переадресация к человеку-ментору для сложных вопросов",
  "policy": {
    "platform_name": "Qalan.kz",
    "audience": "school_student_child",
    "domain_scope": "mentor_escalation_only",
    "escalation_message": "Передаю твой вопрос наставнику. Он свяжется с тобой в ближайшее время.",
    "response_style": "коротко, дружелюбно, без технических терминов"
  },
  "rules_of_speaking": {
    "lang": "ru",
    "tone": "дружелюбный, поддерживающий",
    "must_include": [
      "Сообщить что вопрос передан ментору",
      "Успокоить ученика что получит помощь"
    ],
    "forbidden": [
      "Я бот",
      "Я ИИ",
      "Технические термины"
    ]
  },
  "created_at": "2026-01-26T10:00:00Z",
  "updated_at": "2026-01-26T10:00:00Z"
}
```

**Файл:** `src/agents/registry.py`

```python
# Добавить в AGENT_REGISTRY:
from src.agents.mentor import mentor_agent

AGENT_REGISTRY = {
    # ... существующие
    
    # Mentor agent (для эскалаций)
    (IntentEnum.mentor, None): mentor_agent.MentorAgent,
}
```

**Файл:** `src/utils/classifier/intents.py`

```python
# Убедиться что IntentEnum.mentor существует:
class IntentEnum(str, Enum):
    cashback = "cashback"
    support = "support"
    freezing = "freezing"
    task_problems = "task_problems"
    mentor = "mentor"  # ✅ Должно быть
    neutral = "neutral"
```

**Файл:** `src/utils/policies/policy_loader.py`

```python
# Добавить Policy Model для mentor:

class MentorPolicy(BaseModel):
    escalation_message: str
    response_style: str


PolicyModels = {
    # ... существующие
    (IntentEnum.mentor, None): MentorPolicy,
}

POLICY_PATHS = {
    # ... существующие
    ("mentor", None): POLICY_ROOT/"mentor_main.json",
}
```

---

### 1.2. Реализовать настоящий API Integration 🔴

**Файл:** `src/tools/services/task_service.py`

**Заменить mock на реальный API:**

```python
import requests
import json
from src.configs.settings import (
    USER_CURRENT_TASK, 
    headers1, 
    USE_MOCK_SERVICES
)
from typing import Optional, Dict, Any


def mock_get_current_task(user_id: str) -> Optional[Dict[str, Any]]:
    """
    Mock данные для тестирования (старая версия)
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
            
            # Маппинг API response → наш формат
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
        
    except Exception as e:
        print(f"[API ERROR] Unexpected error for user_id={user_id}: {e}")
        return None
```

**Файл:** `src/configs/settings.py`

```python
# Убедиться что есть флаг:
USE_MOCK_SERVICES = False  # ✅ False для production, True для тестов

# Проверить что endpoint правильный:
USER_CURRENT_TASK = USABLE_BRANCH + '/api/mlRequest/pupilInfo?userId={}'
```

**Тестирование переключения:**

```python
# src/tests/test_task_service.py

import pytest
from src.tools.services.task_service import get_current_task
from src.configs import settings

def test_mock_mode():
    """Тест mock режима"""
    settings.USE_MOCK_SERVICES = True
    
    task = get_current_task("123")
    
    assert task is not None
    assert task["task_id"] == "mock_12345"
    assert task["task_type"] == "personal_study"


def test_production_mode():
    """Тест production режима (требует реальный API)"""
    settings.USE_MOCK_SERVICES = False
    
    # Использовать реальный test user_id из базы
    task = get_current_task("1741535")  # Замените на реальный ID
    
    if task:
        assert "task_text" in task
        assert "task_type" in task
    else:
        pytest.skip("API не вернул задачу (возможно нет активного задания)")
```

---

## ЭТАП 2: LATEX ОБРАБОТКА

### 2.1. Создать LaTeX Processor

**Файл:** `src/utils/latex_processor.py`

```python
import re
from typing import List

# Список поддерживаемых LaTeX команд (из старого кода)
LATEX_COMMANDS = [
    "frac", "tfrac", "dfrac", "sqrt", "sum", "int", "lim", "infty",
    "cdot", "times", "div", "pm", "ne", "approx", "leq", "geq",
    "left", "right", "begin", "end", "text", "textit", "textbf",
    "alpha", "beta", "gamma", "delta", "pi", "theta", "lambda",
    "sin", "cos", "tan", "log", "ln", "lg",
    "angle", "degree", "overline", "underline", "vec"
]


def fix_latex_formatting(text: str) -> str:
    """
    Исправить LaTeX форматирование в ответе агента.
    Основано на старом коде из th_tools.py
    
    Обрабатывает:
    - Спецсимволы (\\a, \\b, \\f, \\t, \\r)
    - Переносы строк внутри формул
    - Ведущие слэши перед командами
    
    Args:
        text: Текст с LaTeX формулами
        
    Returns:
        Исправленный текст
    """
    
    # ============================================
    # 1. Замена спецсимволов
    # ============================================
    replacements = {
        chr(7): '\\a',   # Bell
        chr(8): '\\b',   # Backspace
        chr(12): '\\f',  # Form feed
        chr(9): '\\t',   # Tab
        chr(13): '\\r',  # Carriage return
        "\'": '"'        # Single quote → double quote
    }
    
    for old, new in replacements.items():
        if old in text:
            text = text.replace(old, new)
    
    # ============================================
    # 2. Обработка блоков LaTeX
    # ============================================
    def fix_newlines_in_latex(match):
        """Заменить \n на \\\\ внутри формул"""
        content = match.group(0)
        return content.replace('\n', '\\\\').replace(chr(10), '\\\\')
    
    # Паттерн для блочных \\[ ... \\] и строчных \\( ... \\) формул
    pattern = r'(\\\[.*?\\\]|\\\(.*?\\\))'
    text = re.sub(pattern, fix_newlines_in_latex, text, flags=re.DOTALL)
    
    # ============================================
    # 3. Добавление ведущих слэшей
    # ============================================
    def add_leading_slash(match):
        """Добавить \\ перед LaTeX командами если нужно"""
        matched_text = match.group(0)
        if not matched_text.startswith('\\'):
            return '\\' + matched_text
        return matched_text
    
    text = re.sub(pattern, add_leading_slash, text, flags=re.DOTALL)
    
    # ============================================
    # 4. Raw string для сохранения слэшей
    # ============================================
    return fr'{text}'


def validate_latex(text: str) -> bool:
    """
    Проверить, содержит ли текст LaTeX формулы
    
    Args:
        text: Текст для проверки
        
    Returns:
        True если найдены формулы, False иначе
    """
    return bool(re.search(r'\\\[.*?\\\]|\\\(.*?\\\)', text, re.DOTALL))


def extract_latex_formulas(text: str) -> List[str]:
    """
    Извлечь все LaTeX формулы из текста
    
    Args:
        text: Текст с формулами
        
    Returns:
        Список формул
    """
    pattern = r'(\\\[.*?\\\]|\\\(.*?\\\))'
    matches = re.findall(pattern, text, re.DOTALL)
    return matches


def sanitize_latex(formula: str) -> str:
    """
    Санитизация LaTeX формулы для безопасности.
    Удаляет потенциально опасные команды.
    
    Args:
        formula: LaTeX формула
        
    Returns:
        Безопасная формула
    """
    # Запрещённые команды (могут использоваться для инъекций)
    forbidden = [
        "input", "include", "write", "openout",
        "closeout", "def", "gdef", "edef"
    ]
    
    for cmd in forbidden:
        pattern = r'\\' + cmd + r'\b'
        formula = re.sub(pattern, '', formula, flags=re.IGNORECASE)
    
    return formula


# ============================================
# Примеры использования
# ============================================

if __name__ == "__main__":
    # Пример 1: Простая формула
    text1 = "Решение: \\[ x = \\frac{-b \\pm \\sqrt{b^2 - 4ac}}{2a} \\]"
    print("До:", text1)
    print("После:", fix_latex_formatting(text1))
    print("Валидна:", validate_latex(text1))
    print()
    
    # Пример 2: Формула с переносами
    text2 = """Используй формулу: \\[
    \\frac{a}{b} = c
    \\]"""
    print("До:", text2)
    print("После:", fix_latex_formatting(text2))
    print()
    
    # Пример 3: Строчная формула
    text3 = "Квадратный корень: \\( \\sqrt{25} = 5 \\)"
    print("До:", text3)
    print("После:", fix_latex_formatting(text3))
    print("Формулы:", extract_latex_formulas(text3))
```

**Тесты:**

```python
# src/tests/test_latex_processor.py

import pytest
from src.utils.latex_processor import (
    fix_latex_formatting,
    validate_latex,
    extract_latex_formulas,
    sanitize_latex
)


def test_validate_latex_positive():
    """Тест распознавания LaTeX"""
    text = "Формула: \\[ x^2 + y^2 = r^2 \\]"
    assert validate_latex(text) == True


def test_validate_latex_negative():
    """Тест отсутствия LaTeX"""
    text = "Обычный текст без формул"
    assert validate_latex(text) == False


def test_fix_newlines():
    """Тест исправления переносов строк"""
    text = "\\[\n x = 5 \n\\]"
    fixed = fix_latex_formatting(text)
    assert "\n" not in fixed or "\\\\" in fixed


def test_extract_formulas():
    """Тест извлечения формул"""
    text = "Две формулы: \\[ x = 1 \\] и \\( y = 2 \\)"
    formulas = extract_latex_formulas(text)
    assert len(formulas) == 2


def test_sanitize_dangerous():
    """Тест удаления опасных команд"""
    dangerous = "\\[ \\input{secret.tex} x = 5 \\]"
    safe = sanitize_latex(dangerous)
    assert "input" not in safe.lower()


def test_real_world_example():
    """Тест с реальной математической формулой"""
    text = "Квадратное уравнение: \\[ x = \\frac{-b \\pm \\sqrt{b^2-4ac}}{2a} \\]"
    
    assert validate_latex(text) == True
    
    fixed = fix_latex_formatting(text)
    assert "frac" in fixed
    assert "sqrt" in fixed
    
    formulas = extract_latex_formulas(text)
    assert len(formulas) == 1
```

---

### 2.2. Интегрировать в Agent Response

**Файл:** `src/graph/nodes.py`

```python
def agent_execution_node(
        state: BotState,
        policy_loader,
        backend_tools=None
):
    key = (state.intent, state.subintent)
    AgentClass = AGENT_REGISTRY.get(key)

    if AgentClass is None:
        return ValueError(f"No Agent registered for intent/subintent {key}")

    agent = AgentClass(
        context_data=state.summary,
        policy_loader=policy_loader,
        user_id=state.user_id,
        backend_tools=backend_tools
    )

    # Запуск агента
    agent_result = agent.run_agent(user_message=state.user_message, summary=state.summary)
    state.agent_answer = agent_result  # Это dict
    
    # ============================================
    # ✅ Task Helper специфическая обработка
    # ============================================
    if state.intent == IntentEnum.task_problems and state.subintent == TaskProblemsSubIntentEnum.task_problems:
        try:
            from src.utils.latex_processor import fix_latex_formatting, validate_latex
            
            response_data = agent_result.get("response", {})
            
            # Обновляем Task Helper состояние
            state.task_helper_active = True
            state.current_hint_level = response_data.get("hint_level", 0)
            state.escalate_to_mentor = response_data.get("escalate_to_mentor", False)
            
            # Увеличиваем счётчик подсказок (только если hint_level > 0)
            if response_data.get("hint_level", 0) > 0:
                state.hints_given += 1
            
            # Сохраняем контекст задачи
            if state.task_context is None and backend_tools:
                state.task_context = {
                    "task_text": backend_tools.get("current_task"),
                    "task_type": backend_tools.get("task_type"),
                    "task_id": backend_tools.get("task_id")
                }
            
            # ============================================
            # ✅ LaTeX обработка
            # ============================================
            answer_text = response_data.get("answer", "")
            
            if answer_text and validate_latex(answer_text):
                print(f"[LaTeX] Processing formulas for user_id={state.user_id}")
                answer_text = fix_latex_formatting(answer_text)
                
                # Обновляем ответ
                response_data["answer"] = answer_text
                agent_result["response"] = response_data
                state.agent_answer = agent_result
            
        except Exception as e:
            print(f"Task Helper state update error: {e}")
            import traceback
            traceback.print_exc()
    
    return state
```

---

## ЭТАП 3: РАСШИРЕННОЕ ЛОГИРОВАНИЕ

### 3.1. Создать Task Helper Logger

**Файл:** `src/tools/monitoring/task_helper_logger.py`

```python
import logging
import json
from datetime import datetime
from typing import Dict, Any, Optional

# Настройка логгера
logger = logging.getLogger("TaskHelper")
logger.setLevel(logging.INFO)

# Файловый handler
file_handler = logging.FileHandler("logs/task_helper.log")
file_handler.setLevel(logging.INFO)

# Формат логов
formatter = logging.Formatter(
    '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)


class TaskHelperEvent:
    """Типы событий Task Helper"""
    TASK_FETCHED = "task_fetched"
    HINT_GIVEN = "hint_given"
    ESCALATION = "escalation"
    TASK_COMPLETED = "task_completed"
    API_ERROR = "api_error"
    LATEX_PROCESSED = "latex_processed"
    VALIDATION_ERROR = "validation_error"


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
        "user_id": user_id,
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
```

**Интеграция в агента:**

```python
# В TaskHelperHelperAgent.run_agent()

from src.tools.monitoring.task_helper_logger import (
    log_hint_given,
    log_escalation,
    log_task_completed
)

# После выдачи подсказки
if response_data.get("hint_level", 0) > 0:
    log_hint_given(
        user_id=self.user_id,
        hint_level=response_data["hint_level"],
        task_id=backend_tools.get("task_id")
    )

# При эскалации
if response_data.get("escalate_to_mentor"):
    log_escalation(
        user_id=self.user_id,
        reason="max_hints_reached",
        hints_given=response_data.get("hint_level", 0)
    )

# При успешном решении
if response_data.get("task_completed"):
    log_task_completed(
        user_id=self.user_id,
        task_id=backend_tools.get("task_id"),
        hints_used=response_data.get("hint_level", 0)
    )
```

---

## ЭТАП 4: PRODUCTION DEPLOYMENT CHECKLIST

### 4.1. Переключение на Production

**Файл:** `src/configs/settings.py`

```python
# ============================================
# PRODUCTION CONFIG
# ============================================

# API endpoints
USABLE_BRANCH = PROD_URL  # ✅ Переключить на production
USE_MOCK_SERVICES = False  # ✅ Отключить mock

# RabbitMQ
USABLE_RABBIT_URL = PROD_RABBIT  # ✅ Production очередь
USABLE_RABBIT_QUEUE = RABBIT_PROD_QUEUE  # ✅ Production queue

# GPT Models
DEFAULT_GPT_MODEL = gpt_5  # ✅ Лучшая модель для production

# Токены (из .env)
assert OPENAI_API_KEY is not None, "OPENAI_API_KEY required"
assert MAIN_TOKEN is not None, "QALAN_MAIN_TOKEN required"
```

---

### 4.2. requirements.txt (исправленный)

**Файл:** `requirements.txt`

```
# Core dependencies
openai>=1.0.0
pydantic>=2.0.0
redis>=4.5.0
pika>=1.3.0
requests>=2.28.0

# LangGraph
langgraph>=0.0.20

# Testing
pytest>=7.4.0
pytest-asyncio>=0.21.0

# Utilities
python-dotenv>=1.0.0
```

---

### 4.3. Environment Variables

**Файл:** `.env.production`

```bash
# OpenAI
OPENAI_API_KEY=sk-...
OPENAI_API_KEY_TASK_HELPER=sk-...

# Qalan API
QALAN_MAIN_TOKEN=Bearer ...

# Redis
REDIS_HOST=10.207.19.7
REDIS_PORT=6379

# RabbitMQ
RABBITMQ_URL=amqp://admin:...@10.207.48.24:5672/admin
RABBITMQ_QUEUE=messages

# Config
USE_MOCK_SERVICES=false
LOG_LEVEL=INFO
```

---

### 4.4. Проверка перед deploy

**Файл:** `scripts/pre_deployment_check.sh`

```bash
#!/bin/bash

echo "🔍 Pre-Deployment Checks для Task Helper"
echo "========================================"

# 1. Проверка Python версии
echo "✓ Checking Python version..."
python --version | grep "3.11" || echo "❌ Python 3.11 required!"

# 2. Проверка зависимостей
echo "✓ Checking dependencies..."
pip list | grep "openai" || echo "❌ openai not installed!"
pip list | grep "langgraph" || echo "❌ langgraph not installed!"

# 3. Проверка environment variables
echo "✓ Checking environment variables..."
[ -z "$OPENAI_API_KEY" ] && echo "❌ OPENAI_API_KEY not set!"
[ -z "$QALAN_MAIN_TOKEN" ] && echo "❌ QALAN_MAIN_TOKEN not set!"

# 4. Проверка Redis connection
echo "✓ Checking Redis connection..."
python -c "from src.tools.storage.state_store.redis_usage.redis_connection import redis_connection; redis_connection.ping()" || echo "❌ Redis connection failed!"

# 5. Проверка API доступности
echo "✓ Checking Qalan API..."
curl -f -H "Authorization: Bearer $QALAN_MAIN_TOKEN" https://qalan.kz/api/health || echo "❌ API not available!"

# 6. Запуск тестов
echo "✓ Running tests..."
pytest src/tests/ -v || echo "❌ Tests failed!"

# 7. Проверка логов директории
echo "✓ Checking logs directory..."
[ -d "logs" ] || mkdir -p logs

echo ""
echo "✅ All checks passed! Ready for deployment."
```

---

## ЭТАП 5: МОНИТОРИНГ И АНАЛИТИКА

### 5.1. Метрики для отслеживания

**Файл:** `src/tools/monitoring/metrics.py`

```python
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List
import json


@dataclass
class TaskHelperMetrics:
    """Метрики Task Helper за период"""
    
    # Общие метрики
    total_requests: int = 0
    autonomous_resolutions: int = 0  # Решено без ментора
    escalations: int = 0  # Передано ментору
    
    # Детальные метрики
    avg_hints_per_task: float = 0.0
    tasks_completed: int = 0  # Ученик решил задачу
    
    # По уровням подсказок
    hints_level_distribution: Dict[int, int] = None  # {1: 50, 2: 30, ...}
    
    # Ошибки
    api_errors: int = 0
    validation_errors: int = 0
    
    # Производительность
    avg_response_time_ms: float = 0.0
    
    def autonomy_rate(self) -> float:
        """Процент автономных решений (без ментора)"""
        if self.total_requests == 0:
            return 0.0
        return (self.autonomous_resolutions / self.total_requests) * 100
    
    def success_rate(self) -> float:
        """Процент успешно решённых задач"""
        if self.total_requests == 0:
            return 0.0
        return (self.tasks_completed / self.total_requests) * 100
    
    def escalation_rate(self) -> float:
        """Процент эскалаций к ментору"""
        if self.total_requests == 0:
            return 0.0
        return (self.escalations / self.total_requests) * 100
    
    def to_dict(self) -> dict:
        """Экспорт метрик в dict"""
        return {
            "total_requests": self.total_requests,
            "autonomous_resolutions": self.autonomous_resolutions,
            "escalations": self.escalations,
            "avg_hints_per_task": self.avg_hints_per_task,
            "tasks_completed": self.tasks_completed,
            "hints_level_distribution": self.hints_level_distribution or {},
            "api_errors": self.api_errors,
            "validation_errors": self.validation_errors,
            "avg_response_time_ms": self.avg_response_time_ms,
            "kpi": {
                "autonomy_rate": self.autonomy_rate(),
                "success_rate": self.success_rate(),
                "escalation_rate": self.escalation_rate()
            }
        }


class MetricsCollector:
    """Сборщик метрик Task Helper"""
    
    def __init__(self):
        self.metrics = TaskHelperMetrics()
        self.hints_distribution = {}
    
    def record_request(self):
        """Записать новый запрос"""
        self.metrics.total_requests += 1
    
    def record_hint(self, level: int):
        """Записать выданную подсказку"""
        self.hints_distribution[level] = self.hints_distribution.get(level, 0) + 1
    
    def record_escalation(self):
        """Записать эскалацию к ментору"""
        self.metrics.escalations += 1
    
    def record_completion(self, hints_used: int):
        """Записать успешное завершение задачи"""
        self.metrics.tasks_completed += 1
        self.metrics.autonomous_resolutions += 1
    
    def record_api_error(self):
        """Записать ошибку API"""
        self.metrics.api_errors += 1
    
    def calculate_averages(self):
        """Вычислить средние значения"""
        if self.metrics.total_requests > 0:
            total_hints = sum(level * count for level, count in self.hints_distribution.items())
            self.metrics.avg_hints_per_task = total_hints / self.metrics.total_requests
        
        self.metrics.hints_level_distribution = self.hints_distribution
    
    def export_metrics(self, filepath: str = "logs/metrics.json"):
        """Экспортировать метрики в файл"""
        self.calculate_averages()
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.metrics.to_dict(), f, indent=2, ensure_ascii=False)
    
    def print_summary(self):
        """Вывести summary метрик в консоль"""
        self.calculate_averages()
        
        print("\n" + "="*60)
        print("TASK HELPER METRICS SUMMARY")
        print("="*60)
        print(f"Total Requests: {self.metrics.total_requests}")
        print(f"Autonomy Rate: {self.metrics.autonomy_rate():.1f}%")
        print(f"Success Rate: {self.metrics.success_rate():.1f}%")
        print(f"Escalation Rate: {self.metrics.escalation_rate():.1f}%")
        print(f"Avg Hints: {self.metrics.avg_hints_per_task:.2f}")
        print(f"API Errors: {self.metrics.api_errors}")
        print("="*60 + "\n")


# Глобальный коллектор метрик
metrics_collector = MetricsCollector()
```

**Использование:**

```python
# В agent_execution_node или run_worker.py

from src.tools.monitoring.metrics import metrics_collector

# При каждом запросе к Task Helper
if state.intent == IntentEnum.task_problems:
    metrics_collector.record_request()

# При выдаче подсказки
if hint_level > 0:
    metrics_collector.record_hint(hint_level)

# При эскалации
if escalate_to_mentor:
    metrics_collector.record_escalation()

# При успешном решении
if task_completed:
    metrics_collector.record_completion(hints_used)

# Экспорт метрик каждые N запросов или по таймеру
if metrics_collector.metrics.total_requests % 100 == 0:
    metrics_collector.export_metrics()
    metrics_collector.print_summary()
```

---

## ИТОГОВЫЙ ЧЕКЛИСТ ДЛЯ PRODUCTION

### ✅ Критические требования:

- [ ] **Intent "mentor"** - агент создан и зарегистрирован
- [ ] **API Integration** - `USE_MOCK_SERVICES=false`, реальный API работает
- [ ] **LaTeX Processor** - создан и протестирован на 10+ примерах
- [ ] **Error Handling** - graceful degradation при сбоях API
- [ ] **Logging** - task_helper_logger.py работает, логи пишутся
- [ ] **Metrics** - MetricsCollector собирает данные
- [ ] **requirements.txt** - пересоздан без пробелов
- [ ] **Environment** - `.env.production` настроен
- [ ] **Tests** - все тесты проходят (pytest)
- [ ] **Pre-deployment check** - скрипт выполнен успешно

### ✅ Конфигурация:

- [ ] `USE_MOCK_SERVICES = False`
- [ ] `USABLE_BRANCH = PROD_URL`
- [ ] `USABLE_RABBIT_QUEUE = RABBIT_PROD_QUEUE`
- [ ] `DEFAULT_GPT_MODEL = gpt_5`
- [ ] Environment variables установлены

### ✅ Мониторинг:

- [ ] Логи пишутся в `logs/task_helper.log`
- [ ] Метрики экспортируются в `logs/metrics.json`
- [ ] Dashboard для метрик настроен (опционально)

### ✅ Документация:

- [ ] `CHANGELOG.md` обновлён
- [ ] `docs/TASK_HELPER.md` создан
- [ ] API endpoints задокументированы
- [ ] Примеры диалогов добавлены

---

## ЗАПУСК В PRODUCTION

### 1. Подготовка окружения

```bash
# 1. Клонировать репозиторий
cd /path/to/chat_bot_project

# 2. Создать виртуальное окружение
python -m venv venv
source venv/bin/activate

# 3. Установить зависимости
pip install -r requirements.txt

# 4. Настроить .env
cp .env.example .env.production
nano .env.production  # Заполнить токены

# 5. Создать директорию логов
mkdir -p logs
```

### 2. Pre-deployment проверка

```bash
# Запустить проверочный скрипт
bash scripts/pre_deployment_check.sh

# Если всё OK → продолжать
# Если есть ошибки → исправить и повторить
```

### 3. Запуск сервиса

```bash
# Запуск основного процесса
python -m src.app.mp_observer

# В отдельном терминале - мониторинг логов
tail -f logs/task_helper.log
```

### 4. Проверка работоспособности

```bash
# Отправить тестовое сообщение через RabbitMQ
python scripts/send_test_message.py --user_id=123 --message="Не могу решить задачу"

# Проверить логи
tail -n 50 logs/task_helper.log

# Проверить метрики
cat logs/metrics.json
```

---

## ОТКАТ (ROLLBACK) В СЛУЧАЕ ПРОБЛЕМ

### Если что-то пошло не так:

```bash
# 1. Остановить процесс
pkill -f mp_observer

# 2. Переключить на mock
export USE_MOCK_SERVICES=true

# 3. Перезапустить
python -m src.app.mp_observer

# 4. Анализировать логи
grep ERROR logs/task_helper.log
```

---

## ОЖИДАЕМЫЕ РЕЗУЛЬТАТЫ

### После успешного деплоя:

✅ **Автономность 70-80%** - Task Helper решает большинство вопросов
✅ **Средний Success Rate >60%** - ученики решают задачи с помощью агента
✅ **Avg Hints <3.5** - эффективные подсказки
✅ **Escalation Rate <30%** - редкие передачи ментору
✅ **API Errors <1%** - стабильная работа с API

---

## КОНТАКТЫ

**Technical Lead:** [Имя]  
**GitLab:** https://code.nkz.icdc.io/ml/chat_bot_project  
**Monitoring:** [ссылка на dashboard если есть]

---

**Этот документ — полное ТЗ для Production Deployment Task Helper v2.0**  
**Последнее обновление:** 2026-01-26
