import json
from typing import Dict, Optional

from src.tools.services.push_reactions.finished_task import evaluate_problems
from src.tools.services.push_reactions.not_finished_task import finish_personal_study

PROMISS_TEMPLATES = [
    "new_notify_pupil_about_finish_personal_study_third_2",
    "new_notify_pupil_about_finish_personal_study_second_2",
    "new_notify_pupil_about_finish_personal_study",
    "new_notify_pupil_about_finish_personal_study_first_2",
    "new_notify_pupil_about_finish_personal_study_first",
    "notify_pupil_about_freezing_finish",
    "notify_new_pupil_about_finishing_personal_study_2",
]


def check_message_for_push(input_json: Dict) -> Optional[Dict]:
    full_context_raw = input_json.get("full_context", "[]")
    try:
        full_context = json.loads(full_context_raw) if isinstance(full_context_raw, str) else full_context_raw
    except Exception:
        return None

    # Find last bot message with a template
    last_bot_msg = None
    for msg in reversed(full_context):
        if msg.get("sender_type") in ["Bot", "ML"]:
            last_bot_msg = msg
            break
    if last_bot_msg is None:
        return None

    template = last_bot_msg.get("template")
    user_message = input_json.get("question", "")

    if template == "pupil_review_after_finishing_2":
        return evaluate_problems(user_message)

    if template in PROMISS_TEMPLATES:
        return finish_personal_study(user_message)

    return None
