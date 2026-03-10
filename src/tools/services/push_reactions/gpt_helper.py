import json
import time

from anthropic import Anthropic

from src.configs.settings import ANTHROPIC_API_KEY
from src.utils.prompts.helper_prompts import classify_message_problem_evaluation_prompt
from src.utils.logger import logger


def ask_gpt_for_help(prompt: str, user_input: str):

    client = Anthropic(api_key=ANTHROPIC_API_KEY)
    MODEL_NAME = "claude-sonnet-4-6"
    start_time = time.time()

    response = client.messages.create(
        model=MODEL_NAME,
        max_tokens=500,
        system=prompt,
        messages=[
            {"role": "user", "content": user_input}
        ]
    )

    end_time = time.time()

    result = get_classification(response)

    logger.info("Claude finished in {} seconds".format(end_time - start_time))
    logger.info("Claude response: {} for user text: {}".format(result, user_input))

    return result


def get_classification(response):
    try:
        content = response.content[0].text
        parsed = json.loads(content)
        return parsed.get("response", "unknown")
    except (json.JSONDecodeError, AttributeError, IndexError):
        return "unknown"
