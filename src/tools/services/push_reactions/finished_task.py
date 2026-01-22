from src.tools.services.push_reactions.classify_user_message import classify_finished_task_problem_level_message, pick_random_answer_finished_task_problem_level

def evaluate_problems(user_message: str):
    answer = classify_finished_task_problem_level_message(user_message)
    answer = pick_random_answer_finished_task_problem_level(answer)
    return answer