from src.utils.prompts.classifier_prompts import *
from src.utils.gpt_utils import ask_gpt, validate_response_format, check_type_response, find_subintent_prompt, intent_to_subintent_validator
from src.configs.settings import DEFAULT_GPT_MODEL, gpt_model_4_1
from src.utils.classifier.intents import ValidationLevel


# вызов usable_context прописать уже через вызов с gpt_utils: usable_context = gpt_utils.usable_context(...)
# notice: TODO: if confidence < your_value: 1) intent = neutral, 2) subintent = None
def classify(
        usable_context: list,
        max_attempts: int = 3,
        prompt: str = classifier_base_prompt
                    ):
    def classify_intent(max_tok: int = 600):
        system_message = [{"role": "system", "content": prompt}]
        messages = system_message + usable_context
        classifier_response = ask_gpt(messages=messages,
                                      max_tok=max_tok,
                                      model_gpt=gpt_model_4_1)

        # notice: delete_after:
        print(f"classifier_intent_response: {classifier_response}")

        return classifier_response

    def classify_subintent(max_tok: int=600, intent=None):
        subintent_prompt = find_subintent_prompt(intent)
        system_message = [{"role": "system", "content": subintent_prompt}]
        messages = system_message + usable_context
        classifier_response = ask_gpt(messages=messages,
                                      max_tok=max_tok,
                                      model_gpt=gpt_model_4_1)

        return classifier_response

    last_error = None
    intent = None

    for i in range(max_attempts):
        try:
            intent_response = validate_response_format(
                gpt_response=check_type_response(classify_intent()),
                level=ValidationLevel.intent
            )

            intent = intent_response["intent"]
            break

        except ValueError as e:
            last_error = e

        except Exception as e:
            last_error = e
            # continue

    # if "intent" not in locals():
    if intent is None:
        raise ValueError("Intent classification failed")

    if intent == IntentEnum.neutral:
        return {"intent": intent, "subintent": None}

    if intent not in intent_to_subintent_validator.keys():
        return {"intent": intent, "subintent": None}


    subintent = None

    for i in range(max_attempts):
        try:
            subintent_response = validate_response_format(gpt_response=check_type_response(classify_subintent(intent=intent)),
                                                 level=ValidationLevel.subintent,
                                                 intent=intent)
            subintent = subintent_response["subintent"]
            break
            # return {"intent": intent, "subintent": subintent}

        except Exception as e:
            last_error = e
            continue

    return {"intent": intent, "subintent": subintent}

    #     except ValueError as e:
    #         last_error = e
    #
    #     except Exception as e:
    #         last_error = e
    #         continue
    #
    # if last_error is not None:
    #     raise ValueError(f"gpt_response didn't validate: {last_error}") from last_error
    #
    # else:
    #     raise ValueError(f"gpt_response didn't validate, classify_intent function is broken")










