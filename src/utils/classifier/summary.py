from src.utils.prompts.classifier_prompts import summarizer_prompt
from src.utils.gpt_utils import ask_gpt
from src.configs.settings import gpt_model_4o_mini


def summarize(usable_context):
    messages = [
        {"role": "system", "content": summarizer_prompt},
        {"role": "user", "content": str(usable_context)}
    ]

    response = ask_gpt(
        messages=messages,
        max_tok=200,
        model_gpt=gpt_model_4o_mini
    )

    return response


