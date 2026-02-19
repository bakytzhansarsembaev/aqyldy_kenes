from src.tools.services.push_reactions.classify_user_message import classify_not_finished_task_message, \
    pick_random_answer_not_finished_task_problem_level


def finish_personal_study(user_message: str):
    done_date = classify_not_finished_task_message(user_message)
    answer = pick_random_answer_not_finished_task_problem_level(done_date)
    if answer is None:
        return None
    return {"answer": answer, "tag": "promiss"}
