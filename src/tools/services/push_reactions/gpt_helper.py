import json
import time

from openai import OpenAI

from src.configs.settings import OPENAI_API_KEY_BASE
from src.utils.prompts.helper_prompts import classify_message_problem_evaluation_prompt
from src.utils.logger import logger


def ask_gpt_for_help(prompt: str, user_input: str):

    client = OpenAI(api_key=OPENAI_API_KEY_BASE)
    MODEL_NAME = "gpt-5.1"
    start_time = time.time()


    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": user_input}
        ],
        max_completion_tokens=500
    )

    end_time = time.time()

    result = get_classification(response)

    logger.info("GPT finished in {} seconds".format(end_time - start_time))
    logger.info("GPT response: {} for user text: {}".format(result, user_input))

    return result


def get_classification(completion):
    try:
        content = completion.choices[0].message.content
        parsed = json.loads(content)
        return parsed.get("response", "unknown")
    except (json.JSONDecodeError, AttributeError, IndexError):
        return "unknown"


