from src.tools.storage.state_store.redis_usage.redis_connection import redis_connection
from typing import Dict, Any, Optional
from src.tools.storage.state_store.redis_usage.redis_usage import get_user, save_user
import src.utils.classifier.classifier as clsf
from src.utils.gpt_utils import usable_context
from src.utils.classifier.summary import summarize
import src.agents.registry as rgstr
from src.router.decision_router.graph_state import BotState
from src.utils.policies.policy_loader import PolicyLoader


def test_user_data():
    return {
        "user_id": str(1741535),

        "context": """Bot: Доброе утро! 🌞
Сегодня отличный день, чтобы начать с маленькой победы. Давай выполним задания прямо сейчас — так у тебя останется больше времени для отдыха и любимых дел вечером.
 Bot: НАПОМИНАНИЕ!
Медина, у вас все получится!
Вы уже на пути к успеху!  Завершите задание до 00:00, и пусть еще один шаг приведет вас к новым достижениям🚀
Если же у вас нет возможности выполнить задание, вы можете поставить "заморозку" и сохранить свой день.
Главное – не останавливаться, ведь результат не заставит себя ждать! Не забывайте, менторы всегда рядом, стоит лишь нам написать✨

 Bot: Умничка, Медина!

На сегодня вы завершили свои задания, отличная работа! Ваш ежедневный труд - большая ценность, каждый день вы становитесь все лучше и лучше в математике, мы гордимся вами! Продолжайте в том же духе✨

Если у вас есть какие-либо трудности или вопросы, не стесняйтесь спрашивать, мы всегда рады вам помочь.
Как вы оцениваете задание сегодняшнего дня?

 Bot: Доброе утро! 🌞
Сегодня отличный день, чтобы начать с маленькой победы. Давай выполним задания прямо сейчас — так у тебя останется больше времени для отдыха и любимых дел вечером.
 Pupil: как снять деньги
 Pupil: ?
 Pupil: как снять деньги""",

        "full_context": str([{"date":"2025-11-17 09:57:03","text":"Доброе утро! 🌞\r\nСегодня отличный день, чтобы начать с маленькой победы. Давай выполним задания прямо сейчас — так у тебя останется больше времени для отдыха и любимых дел вечером.","sender_type":"Bot"},{"date":"2025-11-17 18:38:10","text":"НАПОМИНАНИЕ!\nМедина, у вас все получится!\nВы уже на пути к успеху!  Завершите задание до 00:00, и пусть еще один шаг приведет вас к новым достижениям🚀\nЕсли же у вас нет возможности выполнить задание, вы можете поставить \"заморозку\" и сохранить свой день.\nГлавное – не останавливаться, ведь результат не заставит себя ждать! Не забывайте, менторы всегда рядом, стоит лишь нам написать✨\n","sender_type":"Bot"},{"date":"2025-11-17 18:52:55","text":"Умничка, Медина!\n\nНа сегодня вы завершили свои задания, отличная работа! Ваш ежедневный труд - большая ценность, каждый день вы становитесь все лучше и лучше в математике, мы гордимся вами! Продолжайте в том же духе✨\n\nЕсли у вас есть какие-либо трудности или вопросы, не стесняйтесь спрашивать, мы всегда рады вам помочь.\nКак вы оцениваете задание сегодняшнего дня?\n","sender_type":"Bot"},{"date":"2025-11-18 10:01:34","text":"Доброе утро! 🌞\r\nСегодня отличный день, чтобы начать с маленькой победы. Давай выполним задания прямо сейчас — так у тебя останется больше времени для отдыха и любимых дел вечером.","sender_type":"Bot"},{"date":"2025-11-18 15:12:19","text":"как снять деньги","sender_type":"pupil"},{"date":"2025-11-18 15:13:18","text":"?","sender_type":"pupil"},{"date":"2025-11-18 15:15:45","text":"как снять деньги","sender_type":"pupil"}])[1:-1],

        "session_context": str([{"date":"2025-11-18 15:12:19","text":"как снять деньги","sender_type":"pupil"},{"date":"2025-11-18 15:13:18","text":"?","sender_type":"pupil"},{"date":"2025-11-18 15:15:45","text":"как снять деньги","sender_type":"pupil"},{"date":"2025-11-18 15:15:56","text":"как снять деньги","sender_type":"pupil"}])[1:-1]
    }


def test_summarize(test_data: Dict[str, Any] = None):
    if test_data is None:
        test_data = test_user_data()
    summary = summarize(usable_context=test_data["full_context"])
    return summary


def test_classifier(test_data: Dict[str, Any] = None):
    if test_data is None:
        test_data = test_user_data()

    classifier_result = clsf.classify(
        usable_context=usable_context(context=test_data["context"],
                                      session_context=test_data["session_context"],
                                      full_context=test_data["full_context"]),

    )

    return classifier_result


def test_bot_state(test_data: Dict[str, Any] = None):
    if test_data is None:
        test_data = test_user_data()

    # объявим 1 стейт
    state = BotState(
        user_id=test_data["user_id"],
        user_message="как снять деньги"
    )

    # summary
    state.summary = test_summarize(test_data)

    # классификация
    classify_result = test_classifier(test_data)

    # присвоим результат классификации
    state.intent = classify_result["intent"]
    state.subintent = classify_result["subintent"]

    print("STATE: ", chr(10), state.model_dump_json())
    return state


def test_agent_class(test_data: Dict[str, Any] = None):
    if test_data is None:
        test_data = test_user_data()
    print(1)
    state = test_bot_state(test_data)
    print(2)
    key = (state.intent, state.subintent)
    print(3)
    AgentClass = rgstr.AGENT_REGISTRY.get(key)

    if AgentClass is None:
        return ValueError(f"No Agent registered for intent/subintent {key}")

    print(AgentClass.__name__)
    state.selected_agent = AgentClass.__name__

    agent = AgentClass(
        # intent=state.intent,
        # subintent=state.subintent,
        backend_tools={"password": "12345678", "username": "+7-777-111-11-11"},  # фиктивный логин/пароль
        context_data=state.summary,
        policy_loader=PolicyLoader(),
        user_id=state.user_id
    )

    print(4)

    agent_response = agent.run_agent(
        user_message=state.user_message,
        summary=state.summary
        )
    print(agent_response)

    state.agent_answer = agent_response

    print("\nState is: \n", state.model_dump_json())
    return state


def test_update_intent(test_data: Dict[str, Any] = None):
    if test_data is None:
        test_data = test_user_data()

    state = test_agent_class(test_data)
    if state.previous_intent is None:
        state.previous_intent = state.intent
    if state.previous_subintent is None:
        state.previous_subintent = state.subintent
    if state.last_agent is None:
        state.last_agent = state.selected_agent

    # notice: возможно неправильно обработана логика previous_intent/previous_subintent - переписать
    # TODO: реализовать отдельную ветку redis "state:session:*" - для введения state

    state_result = state.model_dump()
    # for key in state_result.
    print("\n\n*****EACH KEY IN STATE*****")
    for key in state_result.keys():
        print(f"\n\n{key}: {state_result[key]}")
    return state


if __name__ == "__main__":
    try:
        redis_connection.info()

    except Exception as redis_connection_problem:
        # change it
        raise ConnectionError(f"no connection redis {redis_connection_problem}") from redis_connection_problem

    import pytest
    pytest.main([__file__, "-v", "-s"])
