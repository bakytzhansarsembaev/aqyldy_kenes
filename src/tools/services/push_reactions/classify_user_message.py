from rapidfuzz import process, fuzz
import re
import random
from src.tools.services.push_reactions.classify_message_tags import evaluation_list_easy, evaluation_list_normal, \
    evaluation_list_hard, responses_today, responses_not_today
from src.tools.services.push_reactions.gpt_helper import ask_gpt_for_help
from src.utils.prompts.helper_prompts import classify_message_problem_evaluation_prompt, \
    classify_message_problem_will_be_done_prompt


def normalize(text: str) -> str:
    text = text.lower()
    text = text.replace('ё', 'е')
    text = text.replace('ң', 'н')
    text = re.sub(r'[^a-zа-я0-9/ ]', '', text)
    return text.strip()

def pick_random_answer_finished_task_problem_level(level: str):
    if level == "easy":
        return random.choice(evaluation_list_easy)
    elif level == "normal":
        return random.choice(evaluation_list_normal)
    elif level == "hard":
        return random.choice(evaluation_list_hard)
    else:
        return None


def classify_finished_task_problem_level_message(user_text: str, threshold=90):
    evaluation_groups = {
        "easy": evaluation_list_easy,
        "normal": evaluation_list_normal,
        "hard": evaluation_list_hard
    }

    normalized_text = normalize(user_text)

    best_score = 0
    best_label = None

    for label, keywords in evaluation_groups.items():
        match, score, _ = process.extractOne(
            normalized_text,
            keywords,
            scorer=fuzz.partial_ratio
        )

        if score > best_score:
            best_score = score
            best_label = label

    if best_score >= threshold:
        return best_label

    return ask_gpt_for_help(classify_message_problem_evaluation_prompt, user_text)

def pick_random_answer_not_finished_task_problem_level(done_date: str):
    if done_date == "today":
        return random.choice(responses_today)
    elif done_date == "not_today":
        return random.choice(responses_not_today)
    else:
        return None


def classify_not_finished_task_message(user_text: str, threshold=80):

    return ask_gpt_for_help(classify_message_problem_will_be_done_prompt, user_text)
