from src.utils.prompts.classifier_prompts import summarizer_prompt
from src.utils.gpt_utils import ask_gpt
from src.configs.settings import claude_sonnet


def summarize(usable_context):
    messages = [
        {"role": "system", "content": summarizer_prompt},
        {"role": "user", "content": str(usable_context)}
    ]

    response = ask_gpt(
        messages=messages,
        max_tok=200,
        model_gpt=claude_sonnet
    )

    return response


