import redis
import json
from src.configs.settings import reddis_host, reddis_port, reddis_password, reddis_username

redis_connection = redis.Redis(host=reddis_host,
                               port=reddis_port,
                               #db=0,
                               decode_responses=True,
                               username=reddis_username,
                               password=reddis_password
)

# def user_key(user_id: str):
#

def save_user(user_id: str, user_data: dict):
    redis_connection.set(user_id, json.dumps(user_data, ensure_ascii=False), ex=7200)


def get_user(user_id: str):
    raw = redis_connection.get(user_id)
    if raw is None:
        return None

    return json.loads(raw)


def delete_session(user_id: str) -> bool:
    """Удаляет сессию пользователя из Redis. Возвращает True если удалено, False если не найдено."""
    deleted = redis_connection.delete(user_id)
    return deleted > 0


def update_user_field():
    pass


