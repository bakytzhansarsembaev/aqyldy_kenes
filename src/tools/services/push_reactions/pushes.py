from typing import Dict, Optional

from src.tools.services.push_reactions.finished_task import evaluate_problems
from src.tools.services.push_reactions.not_finished_task import finish_personal_study


def check_message_for_push(input_json: Dict) -> Optional[Dict]:

    pre_last = input_json[-2]
    date = pre_last['date']
    text = pre_last['text']
    sender_type = pre_last['sender_type']
    if sender_type != 'Bot':
        return None

    template = pre_last['template']

    user_message = input_json[-1]["text"]

    if template is not None:
        if template == "pupil_review_after_finishing_2":
            return evaluate_problems(user_message)
        if template == "new_notify_pupil_about_finish_personal_study_third_2" or template == "new_notify_pupil_about_finish_personal_study_second_2" or template == "new_notify_pupil_about_finish_personal_study" or template == "new_notify_pupil_about_finish_personal_study_first_2" or template == "new_notify_pupil_about_finish_personal_study_first" or template == "notify_pupil_about_freezing_finish" or template == "notify_new_pupil_about_finishing_personal_study_2":
            return finish_personal_study(user_message)
        return None


    return None

