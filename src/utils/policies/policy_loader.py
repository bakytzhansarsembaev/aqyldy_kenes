import json

from pydantic import BaseModel, ValidationError
from datetime import datetime
from typing import Literal, Any, Dict, List
from src.utils.classifier.intents import *
from src.utils.project_paths import POLICY_ROOT
import pathlib
from typing import Optional, Any, Dict, List

class NeutralStub(BaseModel):
    platform_name: str
    audience: str
    domain_scope: str
    primary_goal: str
    response_style: str
    no_pressure_rule: str
    in_scope_triggers: str
    default_first_step: str
    out_of_scope_action: Dict
    missing_context_rule: str
    hard_limits: str


class CashbackWithdraw(BaseModel):
    minimum_withdraw_sum: int
    payout_status_days_approved: int
    payout_status_days_is_considering: int
    currency: Literal["russian_ruble", "kazakhstani_tenge", "uzbekistani_sum"]


class CashbackConditions(BaseModel):
    minimum_withdraw_sum: int
    diamond_explanation: str
    coins_explanation: str

class CashbackHistory(BaseModel):
    response_style: str
    in_scope_questions: str
    out_of_scope_action: str
    data_source_rule: str
    operations_schema: str
    max_operations_to_show: int
    no_operations_message: str
    one_operation_template: str
    two_plus_operations_template: str
    policy_rule_next_day_optional: str
    missing_accrual_explanation_rule:str
    hard_limits: str

class FreezingSetter(BaseModel):
    maximum_freezing_days: int
    last_freezing: datetime
    #дописать


class FreezingRemover(BaseModel):
    last_freezing: datetime
    list_of_freezings: List[datetime]


class FreezingAdvice(BaseModel):
    what_is_freeze_definition: str
    when_to_use_freeze: str
    when_not_to_use_freeze: str
    yearly_freeze_limit_days: int
    monthly_freeze_limit_days: int
    self_service_freeze_steps: str
    freeze_granularity_rule: str
    use_data_sources_rule: str
    backend_tools_may_provide: str
    out_of_scope_examples: str
    out_of_scope_action: str
    missing_limits_rule: str
    hard_limits: str


class FreezingStatusChecker(BaseModel):
    last_freezing: datetime
    list_of_freezings: List[datetime]
    response_style: str
    in_scope_questions: str
    backend_tools_only_rule: str
    backend_tools_may_contain: str
    list_present_rule: str
    empty_list_rule: str
    no_data_rule: str
    specific_date_check_rule: str
    today_check_rule: str
    unknown_format_rule: str
    out_of_scope_examples: str
    out_of_scope_action: str
    hard_limits: str


class SupportEmotional(BaseModel):
    response_style: str
    tone_style: str
    max_clarifying_questions: str
    allowed_topics: str
    default_when_insufficient_context: str
    no_motivation_rule: str
    technical_complaint_action: str
    ui_navigation_action: str
    dangerous_content_rule: str
    hard_limits: str


class SupportMotivation(BaseModel):
    primary_goal: str
    response_style: str
    no_pressure_rule: str
    in_scope_triggers: str
    default_first_step: str
    soft_motivation_phrases_kk: str
    categorical_refusal_signals: str
    out_of_scope_action: str
    missing_context_rule: str
    hard_limits: str


class SupportParentSpeaker(BaseModel):
    response_style: str
    formality_rule: str
    in_scope_topics: str
    out_of_scope_action: str
    use_backend_data_rule: str
    no_data_phrase_kk: str
    no_data_rule: str
    how_to_help_parent_guidance: str
    complaint_handling_rule: str
    concern_handling_rule: str
    tech_issue_rule: str
    hard_limits: str

class TaskHelperMain(BaseModel):
    response_style: str
    routing_logic: str
    clarification_rule: str
    route_to_helper_triggers: List[str]
    route_to_changer_triggers: List[str]
    out_of_scope_action: str
    hard_limits: str


class TaskHelperHelper(BaseModel):
    help_style: str
    max_hints_per_task: int
    response_style: str
    step_by_step_rule: str
    hint_progression: str
    praise_rule: str
    forbidden_actions: List[str]
    allowed_actions: List[str]
    if_student_stuck_rule: str
    if_asks_direct_answer: str
    out_of_scope_action: str
    hard_limits: str


class TaskHelperChanger(BaseModel):
    response_style: str
    when_task_too_hard: str
    when_technical_issue: str
    cannot_change_task_rule: str
    available_options: List[str]
    empathy_rule: str
    out_of_scope_examples: str
    out_of_scope_action: str
    hard_limits: str

# class SupportTechProblems(BaseModel):

# class SupportNavigation(BaseModel):


PolicyModels = {
    # заглушка для непроявленных или ненаписанных политик
    (IntentEnum.neutral, NeutralSubIntentEnum.stub): NeutralStub,
    # cashback
    (IntentEnum.cashback, CashbackSubIntentEnum.withdrawal): CashbackWithdraw,
    (IntentEnum.cashback, CashbackSubIntentEnum.conditions): CashbackConditions,
    (IntentEnum.cashback, CashbackSubIntentEnum.cashback_history): CashbackHistory,
    # freezing
    (IntentEnum.freezing, FreezingSubIntentEnum.freezing_remover): FreezingRemover,
    (IntentEnum.freezing, FreezingSubIntentEnum.freezing_setter): FreezingSetter,
    (IntentEnum.freezing, FreezingSubIntentEnum.freezing_advice): FreezingAdvice,
    (IntentEnum.freezing, FreezingSubIntentEnum.freezing_status_check): FreezingStatusChecker,
    # support
    (IntentEnum.support, SupportSubIntentEnum.emotional): SupportEmotional,
    (IntentEnum.support, SupportSubIntentEnum.motivation): SupportMotivation,
    (IntentEnum.support, SupportSubIntentEnum.parent_speaker): SupportParentSpeaker,
    # task helper
    (IntentEnum.task_problems, None): TaskHelperMain,
    (IntentEnum.task_problems, TaskProblemsSubIntentEnum.task_problems): TaskHelperHelper,
    (IntentEnum.task_problems, TaskProblemsSubIntentEnum.change_task): TaskHelperChanger,
    # (IntentEnum.support, SupportSubIntentEnum.navigation): SupportNavigation,
    # (IntentEnum.support, SupportSubIntentEnum.tech_problems): SupportTechProblems,
                }


class IntentPolicy(BaseModel):
    intent: str
    subintent: Optional[str]
    version: str
    owner: str
    description: str
    policy: Any
    rules_of_speaking: Dict[str, Any]
    created_at: datetime
    updated_at: datetime


POLICY_PATHS = {
    ("cashback", "conditions"): POLICY_ROOT/"cashback_conditions.json",
    ("cashback", "withdrawal"): POLICY_ROOT/"cashback_withdrawal.json",
    ("cashback", "history"): POLICY_ROOT/"cashback_history.json",

    ("freezing", "freezing_remover"): POLICY_ROOT/"freezing_remover.json",
    ("freezing", "freezing_setter"): POLICY_ROOT/"freezing_setter.json",
    ("freezing", "freezing_adviser"): POLICY_ROOT/"freezing_adviser.json",
    ("freezing", "freezing_status_checker"): POLICY_ROOT/"freezing_status.json",

    ("support", "support_emotional"): POLICY_ROOT/"support_emotional.json",
    ("support", "support_motivation"): POLICY_ROOT/"support_motivation.json",
    ("support", "support_parent_speaker"): POLICY_ROOT/"support_parent_speaker.json",
    ("support", "support_technical"): POLICY_ROOT/"support_tech_problems.json",
    ("support", "support_navigation"): POLICY_ROOT/"support_navigation.json",

    ("task_problems", None): POLICY_ROOT/"task_helper_main.json",
    ("task_problems", "task_problems"): POLICY_ROOT/"task_helper_helper.json",
    ("task_problems", "change_task"): POLICY_ROOT/"task_helper_changer.json",
}


class PolicyLoader:
    def __init__(self):
        self._cache: Dict[str, Any]

    def _load_policy(self, path: str | pathlib.Path) -> IntentPolicy:
        p = pathlib.Path(path).expanduser()
        raw: Dict[str, Any] = json.loads(p.read_text(encoding='utf-8'))

        for key in (
                "intent", "subintent", "version", "owner", "description",
                "policy", "rules_of_speaking", "created_at", "updated_at"
                     ):

            if key not in raw:
                raise KeyError(f"missing key {key} in policy file :{p}")

        intent = raw["intent"]
        subintent = raw["subintent"]

        model_cls = self._check_policy_models(intent, subintent)
        if model_cls is None:
            raise KeyError(f"No PolicyModel registered for ({intent}, {subintent})")

        # валидация загруженных политик (проверка политики по ключам BaseModel и по типам):
        try:
            policy_obj = model_cls(**raw["policy"])

        except ValidationError as e:
            raise ValueError(f"Invalid policy loaded for ({intent}, {subintent}): {e}")

        #здесь должен быть кусок кода проверки updated_at и created_at - пока не критично

        return IntentPolicy(
            intent=intent,
            subintent=subintent,
            version=raw["version"],
            owner=raw["owner"],
            description=raw["description"],
            policy=policy_obj,
            rules_of_speaking=raw["rules_of_speaking"],
            created_at=raw["created_at"],
            updated_at=raw["updated_at"]
        )

    def _check_policy_models(self, intent: str, subintent: str):
        # сопоставляем субинтент с интентом в соответствии с PolicyModels.
        for (intent_enum, subintent_enum), model_cls in PolicyModels.items():
            if self.policy_enum_match(intent_enum, intent) and self.policy_enum_match(subintent_enum, subintent):
                return model_cls

        return None

    def get_for(self, intent, subintent):
        key = (intent, subintent)
        if key not in POLICY_PATHS:
            # notice: delete after tests
            stub_policy_path = POLICY_ROOT/"stub_policy_for_poteryashkins.json"
            return self._load_policy(stub_policy_path)

            # notice: TODO: изменить возврат несуществующих политик, либо создать политики для всех субагентов
            # raise KeyError(f"Policy path for {key} is not exists")
        path = POLICY_PATHS[key]

        return self._load_policy(path)

    @staticmethod
    def policy_enum_match(enum_member, value_str: str) -> bool:
        # проверка соответствия для интентов и сабинтентов
        return getattr(enum_member, "value", None) == value_str
