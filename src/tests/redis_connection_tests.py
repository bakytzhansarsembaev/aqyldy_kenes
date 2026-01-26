import pytest
from src.tools.storage.state_store.redis_usage.redis_connection import redis_connection
from typing import Dict, Any, Optional
from src.tools.storage.state_store.redis_usage.redis_usage import get_user, save_user


# NOTICE: для CI/CD - обязательно в будущем добавь pytest.fixture() для поднятия redis_connection либо через
# мок, либо через прямое подключения redis/rabbit,
# а пока что redis_connection отправлю через if __name__ == __main__
#def check_reddis_connection():


def test_user_data():
    user_data = {
        "user_id": "1001",
        "intent": "cashback",
        "subintent": "withdrawal",
        "language": "kaz",
        "context": "Хочу снять кэшбэк",
        "full_context": "Хочу снять кэшбэк",
        "session_context": "Хочу снять кэшбэк",
    }
    return user_data


@pytest.mark.redis
def test_save_data(test_data: Dict[str, Any] = None):
    if test_data is None:
        test_data = test_user_data()

    try:
        save_user(test_data["user_id"], test_data)
        # проверка записи данных
        got = get_user(test_data["user_id"])
        if got is None:
            raise ValueError(f"Ключ не записался в Редис")

    except Exception as e:
        # print(e)
        raise


@pytest.mark.redis
def test_get_data(test_data: Dict[str, Any] = None):
    if test_data is None:
        test_data = test_user_data()

    try:
        return get_user(test_data["user_id"])

    except Exception as e:
        # print(e)
        raise


@pytest.mark.redis
def test_clean_up_data(test_data: Dict[str, Any] = None):
    if test_data is None:
        test_data = test_user_data()

    try:

        deleted_data = redis_connection.delete(test_data["user_id"])

        if deleted_data == 0:
            raise KeyError("Ключ не найден, возможно удалён раннее")

        got = get_user(test_data["user_id"])
        if deleted_data == 1:
            if got is None:
                return "Данные успешно удалены"

            else:
                raise ValueError("Не могло быть так")

    except Exception as e:
        raise


if __name__ == "__main__":
    try:
        redis_connection.info()

    except Exception as redis_connection_problem:
        # change it
        raise ConnectionError(f"no connection redis {redis_connection_problem}") from redis_connection_problem

    import pytest
    pytest.main([__file__, "-v", "-s"])
