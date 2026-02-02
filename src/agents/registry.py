from src.utils.classifier.intents import *

# notice: По возможности поменять на декоратор - чтобы так не грузить всех агентов
from src.agents.cashback import cashback_main_agent, cashback_withdrawal_agent, cashback_history_agent, cashback_conditions_agent
from src.agents.freezing import freezing_main_agent, freezing_setter_agent, freezing_remover_agent, freezing_adviser_agent, freezing_status_checker_agent
from src.agents.task_helper import task_helper_helper_agent, task_helper_main_agent, task_helper_changer_agent
from src.agents.mentor_support import support_main_agent, support_tech_problem_agent, support_motivation_agent, support_emotional_agent, support_navigation_agent
from src.agents.mentor import mentor_agent
from src.agents import neutral_agent


AGENT_REGISTRY = {
    # notice: при увеличении количества агентов файл опухнет от импортов
    # поэтому нужно будет разработать декоратор для автоматического заполнения реестра
    # или можно рил завернуть в мапу и не париться - пока в процессе решения этого вопроса
    (IntentEnum.neutral, None): neutral_agent.NeutralAgent,
    # cashback agents map:
    (IntentEnum.cashback, None): cashback_main_agent.CashbackMainAgent,
    (IntentEnum.cashback, CashbackSubIntentEnum.withdrawal): cashback_withdrawal_agent.CashbackWithdrawalAgent,
    (IntentEnum.cashback, CashbackSubIntentEnum.conditions): cashback_conditions_agent.CashbackConditionsAgent,
    (IntentEnum.cashback, CashbackSubIntentEnum.cashback_history): cashback_history_agent.CashbackHistoryAgent,
    # freezing agents map:
    (IntentEnum.freezing, None): freezing_main_agent.FreezingMainAgent,
    (IntentEnum.freezing, FreezingSubIntentEnum.freezing_setter): freezing_setter_agent.FreezingSetterAgent,
    (IntentEnum.freezing, FreezingSubIntentEnum.freezing_remover): freezing_remover_agent.FreezingRemoverAgent,
    (IntentEnum.freezing, FreezingSubIntentEnum.freezing_advice): freezing_adviser_agent.FreezingAdviserAgent,
    (IntentEnum.freezing, FreezingSubIntentEnum.freezing_status_check): freezing_status_checker_agent.FreezingStatusCheckerAgent,
    # support agents map:
    (IntentEnum.support, None): support_main_agent.SupportMainAgent,
    (IntentEnum.support, SupportSubIntentEnum.motivation): support_motivation_agent.SupportMotivationAgent,
    (IntentEnum.support, SupportSubIntentEnum.tech_problems): support_tech_problem_agent.SupportTechProblemsAgent,
    (IntentEnum.support, SupportSubIntentEnum.navigation): support_navigation_agent.SupportNavigationAgent,
    (IntentEnum.support, SupportSubIntentEnum.emotional): support_emotional_agent.SupportEmotionalAgent,
    # task problems agents map
    # По умолчанию используем TaskHelperHelperAgent (помощь с задачей), так как это основной кейс
    (IntentEnum.task_problems, None): task_helper_helper_agent.TaskHelperHelperAgent,
    (IntentEnum.task_problems, TaskProblemsSubIntentEnum.task_problems): task_helper_helper_agent.TaskHelperHelperAgent,
    (IntentEnum.task_problems, TaskProblemsSubIntentEnum.change_task): task_helper_changer_agent.TaskHelperChangerAgent,
    # mentor agent (для эскалаций к человеку-ментору)
    (IntentEnum.mentor, None): mentor_agent.MentorAgent,
}
