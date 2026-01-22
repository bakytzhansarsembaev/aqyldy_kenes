from src.tools.services.push_reactions.classify_user_message import classify_not_finished_task_message, \
    pick_random_answer_not_finished_task_problem_level


def finish_personal_study(user_message: str):
    answer = classify_not_finished_task_message(user_message)
    answer = pick_random_answer_not_finished_task_problem_level(answer)
    return answer