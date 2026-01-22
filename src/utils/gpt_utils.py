from openai import OpenAI
from src.configs.settings import OPENAI_API_KEY_BASE, date_format, gpt_5_1, gpt_5_2
from typing import Optional, List, Dict, Any
import re, json, datetime
from src.utils.classifier.intents import CheckIntent, ValidationLevel, IntentEnum, intent_to_subintent_validator
from pydantic import ValidationError
from src.utils.prompts.classifier_prompts import SUBINTENT_PROMPTS

client = OpenAI(api_key=OPENAI_API_KEY_BASE)


def preprocess_context(context):
    try:
        dlg1 = context
        dlg1 = re.sub(r'(\bMentor: |\bBOT: |\bML: |\bmentor: |\bBot: )', r'assistant:', dlg1)
        dlg1 = re.sub(r'(\bPupil: |\bParent: |\bpupil: |\bparent: |/bPupil :)', r'user: ', dlg1)
        dlg1 = re.sub(r':', r': ', dlg1)
        dlg1 = re.sub(r'\n', r' ', dlg1)
        dlg1 = re.split(r'(?=\bassistant: |\buser:)', dlg1)
        dlg1 = [x for x in dlg1 if len(x) > 0]
        dlg1 = [re.split(':', x, maxsplit=1) for x in dlg1]
        # dlg1 = [x for x in dlg1 if len(x) > 0]
        dlg1 = [x for x in dlg1 if len(x) > 1]

        return dlg1

    except Exception as dlg_e:
        print('oshibka v preprocesse', dlg_e)


def eval_contexts(our_list_in_string) -> Optional[List[Dict]]:
    try:
        our_list = eval(our_list_in_string)
    except Exception as first_try_error:
        print("list_of_dicts Error in first try ", first_try_error)
        our_list = None

    if our_list is None:
        try:
            our_list = eval(our_list_in_string.encode('unicode_escape').decode('utf-8'))

        except Exception as second_try_error:
            print("list_of_dicts Error in second try ", second_try_error)
            our_list = None

    return our_list


def ask_gpt(messages: list, max_tok: int, model_gpt: str, response_format=None) -> str:
    print("start ask gpt")
    if model_gpt in [gpt_5_1, gpt_5_2]:
        response = client.chat.completions.create(
            model=model_gpt,
            max_completion_tokens=max_tok,
            messages=messages
        )

    else:
        if response_format is None:
            response = client.chat.completions.create(
                # model="gpt-4o",
                model=model_gpt,
                messages=messages,
                # temperature=0,
                # max_tokens=max_tok,
                top_p=1,
                frequency_penalty=0,
                presence_penalty=0,
                response_format={"type":"text"})
        else:
            response = client.chat.completions.create(
                # model="gpt-4o",
                model=model_gpt,
                # messages= [{"role":"user", "content":"хочу получить валидный JSON"}] + messages,
                messages=messages,
                # temperature=0,
                response_format=response_format,
                # max_tokens=max_tok,
                top_p=1,
                frequency_penalty=0,
                presence_penalty=0
            )


    answer = response.choices[0].message.content

    print("Answer: " + str(answer))
    return answer


# Возможно переделать полностью или удалить эти части, мне не нравятся эти функции.
def contexts_into_gpt_blocks(context_list):
    try:
        messages = []
        for block in context_list:
            sender = re.sub("Bot|mentor|ML", "assistant", block["sender_type"])
            sender = re.sub("pupil|parent", "user", sender)

            messages.append({"role": sender, "content": block["text"]})

        return messages

    except Exception as gpt_blocks_error:
        raise ValueError(f"contexts_into_gpt_blocks failed: {gpt_blocks_error}") from gpt_blocks_error


def cutoff_threshold(threshold_messages_time: int = 2):
    rightnow = datetime.datetime.now()
    today = datetime.datetime.now().date()

    cutoff_9am_today = datetime.datetime.combine(today, datetime.time(hour=9, minute=0, second=0))
    cutoff_2hour_ago = rightnow - datetime.timedelta(hours=threshold_messages_time)

    # Фильтруем сообщения: избавляемся от сообщений прошлых дат или написанных более 2х часов назад
    return max(cutoff_9am_today, cutoff_2hour_ago)


def validate_contexts(session_context, full_context) -> List[Dict[str, Any]]:
    full_context_list = eval_contexts(full_context)
    session_context_list = eval_contexts(session_context)

    if full_context_list is None or session_context_list is None:
        raise ValueError("eval_context returned None")

    else:
        if len(session_context_list) >= len(full_context_list):
            # Если длина контекста сессии >=7 то возвращаем session_context и сразу заменяем sender_type
            return contexts_into_gpt_blocks(session_context_list)

        else:
            time_threshold = cutoff_threshold()

            # Конвертируем строковые даты в объекты datetime
            updated_full_context_list = [
                {**msg, 'date': datetime.datetime.strptime(msg['date'], date_format)}
                for msg in full_context_list
            ]

            # Вырезаем сообщения, написанные раннее чем за 2 часа до нынешнего
            updated_full_context_list = [msg for msg in updated_full_context_list if msg["date"] >= time_threshold]

            # Возвращаем формат с datetime в str
            updated_full_context_list = [
                {**msg, 'date': datetime.datetime.strftime(msg['date'], date_format)}
                for msg in updated_full_context_list
            ]

            # если за 2 последних часа больше сообщений, чем в сессии, то возвращаем udpated_full_context
            if len(updated_full_context_list) >= len(session_context_list):
                return contexts_into_gpt_blocks(updated_full_context_list)

            else:
                return contexts_into_gpt_blocks(session_context_list)


def usable_context(context, full_context, session_context):
    try:
        return validate_contexts(session_context=session_context, full_context=full_context)

    except ValueError as usable_context_error:
        # notice: add_logger
        print("ValueError in usable context: ", usable_context_error)
        return preprocess_context(context=context)


def eval_gpt_response(gpt_response):
    try:
        return eval(gpt_response)

    except Exception as e:
        first_error = e

    try:
        return eval(gpt_response.encode('unicode_escape').decode('utf-8'))

    except Exception as e:
        raise ValueError(f"cannot parse gpt_response: {e}") from e


def check_type_response(gpt_response) -> Dict:
    verifiable_dict = eval_gpt_response(gpt_response)

    if isinstance(verifiable_dict, dict):
        return verifiable_dict

    else:
        raise ValueError(f"parsed value (gpt_response) is not a dict: {gpt_response}")


def validate_response_format(gpt_response: Dict,
                             level: ValidationLevel,
                             intent: Optional[IntentEnum] = None):
    #если мы определяем intent, то проверяем на правильность ответа гпт в соответствии с указанными интентами
    # Intent Level
    if level == ValidationLevel.intent:
        try:
            CheckIntent(**gpt_response)
            return gpt_response
        except ValidationError as e:
            raise ValueError("gpt_response Validation Error") from e

    # Subintent level
    if level == ValidationLevel.subintent:
        if intent is None:
            raise ValueError("Intent context is required for subintent validation")

        try:
            subintent_class = intent_to_subintent_validator[intent]
            subintent_class(**gpt_response)
            return gpt_response

        except ValidationError as e:
            raise ValueError("gpt_response subintent Validation Error") from e
    # notice: здесь я должен буду сделать функцию загрузки из папки policies формать key_value для всех intent-sub-intent связей
    # pass


def find_subintent_prompt(intent: IntentEnum) -> str:
    try:
        return SUBINTENT_PROMPTS[intent]

    except KeyError:
        raise ValueError(f"No subintent prompt found for intent {intent.value}")







def start_asking(dialog_2: str, type_of_ask: str, system_prompt=None, usable_context=None, response_format=None,
                 dict_mini=None):
    if type_of_ask == "big_prompts":
        # Выбор из контекста и session_context
        if usable_context is not None:
            usable_context_list = eval_contexts(usable_context)
            if usable_context_list is not None:
                print("start_asking trouble: session_context_list is None")
                dlg2 = contexts_into_gpt_blocks(usable_context_list)
            else:
                dlg2 = preprocess_context(dialog_2)
        else:
            dlg2 = preprocess_context(dialog_2)

        try:
            messages1 = [{"role": "system", "content": system_prompt}]
            for i in range(len(dlg2)):
                message = {'role': dlg2[i][0], 'content': dlg2[i][1].strip()}
                messages1.append(message)

            gpt_answer_prompt = ask_gpt(messages=messages1,
                                        max_tok=400,
                                        model_gpt="gpt-4.1")
            return gpt_answer_prompt

        except Exception as asking_exception:
            print('Сессия была прервана big_prompts', asking_exception)
            print(dlg2)

    elif type_of_ask == "mini_prompts":
        try:
            gpt_answers = []
            # for key in dict_mini.keys():
            for iteration in range(len(dict_mini)):
                system_prompt = dict_mini[iteration][2]
                mes1 = [{"role": "system", "content": system_prompt}]
                mes1.append({"role": "user", "content": dialog_2})
                gpt_answers.append(ask_gpt(messages=mes1,
                                           max_tok=250,
                                           model_gpt="gpt-4.1-mini")
                                   )

            for i in range(len(gpt_answers)):
                gpt_answers[i] = json.loads(gpt_answers[i])

            return gpt_answers

        except Exception as asking_exception:
            print('Сессия была прервана mini_prompts', asking_exception)
            print(dialog_2)

    elif type_of_ask == "light_model":
        dlg2 = preprocess_context(dialog_2)
        try:
            messages1 = [{"role": "system", "content": system_prompt}]
            for i in range(len(dlg2)):
                message = {'role': dlg2[i][0], 'content': dlg2[i][1].strip()}
                messages1.append(message)

            gpt_answer_prompt = ask_gpt(messages=messages1,
                                        max_tok=200,
                                        model_gpt="gpt-4.1-mini")
            return gpt_answer_prompt

        except Exception as asking_exception:
            print('Сессия была прервана light_model', asking_exception)
            print(dlg2)


# check type ~ json
def is_json(myjson):
  try:
    json.loads(myjson)

  except ValueError as e:
    return False
  return True