from enum import Enum
from pydantic import BaseModel


# Enum for classificator
class ValidationLevel(Enum):
    intent = "intent"
    subintent = "subintent"


# Enums for intents and subintents
class IntentEnum(str, Enum):
    cashback = "cashback"
    support = "support"
    freezing = "freezing"
    task_problems = "task_problems"
    mentor = "mentor"
    neutral = "neutral"


class NeutralSubIntentEnum(str, Enum):
    stub = "stub"  # заглушка


class CashbackSubIntentEnum(str, Enum):
    withdrawal = "withdrawal"
    conditions = "conditions"
    cashback_history = "history"


class FreezingSubIntentEnum(str, Enum):
    freezing_setter = "freezing_setter"
    freezing_remover = "freezing_remover"
    freezing_advice = "freezing_advice"
    freezing_status_check = "freezing_status_check"


class TaskProblemsSubIntentEnum(str, Enum):
    task_problems = "task_problems"
    change_task = "change_task"


class SupportSubIntentEnum(str, Enum):
    tech_problems = "tech_problems"
    motivation = "motivation"
    emotional = "emotional"
    parent_speaker = "parent_speaker"
    navigation = "navigation"


# Validators
class CheckIntent(BaseModel):
    intent: IntentEnum


class CheckCashbackSubIntent(BaseModel):
    subintent: CashbackSubIntentEnum


class CheckFreezingSubIntent(BaseModel):
    subintent: FreezingSubIntentEnum


class CheckTaskProblemsSubIntent(BaseModel):
    subintent: TaskProblemsSubIntentEnum


class CheckSupportSubIntent(BaseModel):
    subintent: SupportSubIntentEnum


# router
intent_to_subintent_validator = {
    IntentEnum.neutral: NeutralSubIntentEnum,
    IntentEnum.cashback: CheckCashbackSubIntent,
    IntentEnum.freezing: CheckFreezingSubIntent,
    IntentEnum.support: CheckSupportSubIntent,
    IntentEnum.task_problems: CheckTaskProblemsSubIntent
}

