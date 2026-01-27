import asyncio
import json
import multiprocessing
import os
import time
import uuid
import threading

import pika
from src.configs.settings import USABLE_RABBIT_QUEUE, USABLE_RABBIT_URL
from src.tools.storage.state_store.redis_usage.redis_connection import redis_connection
from src.utils.gpt_utils import is_json
from src.app import run_worker

rabbit_url = USABLE_RABBIT_URL
rabbit_queue = USABLE_RABBIT_QUEUE
rmq_parameters = pika.URLParameters(rabbit_url)
rmq_parameters.heartbeat = 60
rmq_parameters.blocked_connection_timeout = 300

DEBOUNCE_SECONDS = 0
SLEEP_INTERVAL = 0.1
MAX_WORKERS = 10
DISPATCHER_SLEEP = 0.1
# Lock должен жить дольше средней обработки (иначе lock истечет и запустятся 2 воркера на одного user_id).
# При падении воркера lock отпустится по TTL.
PROCESSING_LOCK_TTL = 120
LOCK_RENEW_INTERVAL = 20
KEY_TTL_SECONDS = 7200
READY_KEY_TTL_SECONDS = 300


def _buffer_key(user_id: str) -> str:
    return f"rabbit:buffer:{user_id}"


def _inflight_key(user_id: str) -> str:
    return f"rabbit:inflight:{user_id}"


def _ready_key(user_id: str) -> str:
    return f"rabbit:ready:{user_id}"


def _last_message_time_key(user_id: str) -> str:
    return f"rabbit:last_message_time:{user_id}"


def _processing_key(user_id: str) -> str:
    return f"rabbit:processing:{user_id}"


_MOVE_ONE_LPOP_RPUSH = redis_connection.register_script(
    """
    local v = redis.call('LPOP', KEYS[1])
    if v then
      redis.call('RPUSH', KEYS[2], v)
    end
    return v
    """
)

_RELEASE_LOCK = redis_connection.register_script(
    """
    if redis.call('GET', KEYS[1]) == ARGV[1] then
      return redis.call('DEL', KEYS[1])
    end
    return 0
    """
)


def _safe_release_lock(lock_key: str, token: str) -> None:
    try:
        _RELEASE_LOCK(keys=[lock_key], args=[token])
    except Exception as e:
        print(f"[LOCK] release error key={lock_key}: {e}")


def start_rabbit_consumer():
    while True:
        try:
            rmq_connection = pika.BlockingConnection(rmq_parameters)
            channel = rmq_connection.channel()
            channel.queue_declare(queue=rabbit_queue, durable=True)
            channel.basic_qos(prefetch_count=5)

            channel.basic_consume(
                queue=rabbit_queue,
                on_message_callback=callback,
                auto_ack=False
            )
            print("Rabbit consuming started")

            channel.start_consuming()

        # except pika.exceptions.AMQPConnectionError as e:
            # print(f"Rabbit connection lost: {e}")

        except Exception as e:
            print(f"Fatal rabbit error: {e}")

        finally:
            print("[RABBIT] connection lost, reconnecting in 5s...")
            try:
                if rmq_connection and rmq_connection.is_open:
                    rmq_connection.close()
            except Exception:
                pass

        time.sleep(5)


def pin_entry_cores():
    os.sched_setaffinity(0, {0, 1})


def pin_workers_cores():
    os.sched_setaffinity(0, set(range(2, 16)))


def _build_final_input_from_messages(input_dicts: list[dict]) -> dict:
    first_input = input_dicts[0]
    concat_user_message = chr(10).join(
        x.get("question", "") for x in input_dicts if x.get("question")
    )
    final_input = first_input.copy()
    final_input["question"] = concat_user_message
    return final_input


def worker_entry(user_id: str, lock_token: str):
    # notice: delete this after tests
    print(f"[WORKER] started user_id={user_id}")

    pin_workers_cores()
    lock_key = _processing_key(user_id)
    inflight_key = _inflight_key(user_id)

    stop_event = threading.Event()

    def _lock_keepalive():
        while not stop_event.wait(LOCK_RENEW_INTERVAL):
            try:
                if redis_connection.get(lock_key) != lock_token:
                    # lock lost/overwritten - не продлеваем чужой lock
                    return
                redis_connection.expire(lock_key, PROCESSING_LOCK_TTL)
            except Exception as e:
                print(f"[LOCK] keepalive error user_id={user_id}: {e}")

    t = threading.Thread(target=_lock_keepalive, daemon=True)
    t.start()

    try:
        raw_messages = redis_connection.lrange(inflight_key, 0, -1) or []
        if not raw_messages:
            print(f"[WORKER] no inflight messages user_id={user_id}")
            return

        try:
            input_dicts = [json.loads(x) for x in raw_messages]
        except Exception as e:
            # Poison batch: чтобы не зациклиться, складываем в deadletter и очищаем inflight.
            print(f"[WORKER] invalid inflight json user_id={user_id}: {e}")
            redis_connection.rpush(f"rabbit:deadletter:{user_id}", *raw_messages)
            redis_connection.delete(inflight_key)
            return

        final_input = _build_final_input_from_messages(input_dicts)

        run_worker.run_event(final_input)

        # Успешно: очищаем inflight (только после run_event)
        redis_connection.delete(inflight_key)
    finally:
        stop_event.set()
        _safe_release_lock(lock_key, lock_token)
        # notice: delete this after tests
        print(f"[WORKER] finished user_id={user_id}")

def callback(channel, method_frame, properties, body_mq):
    # pin_entry_cores()

    try:
        # notice: delete this print after tests
        print("[RABBIT] message recieved from rabbit to callback")
        # 1
        if not is_json(body_mq):
            # Poison message: нельзя распарсить => не requeue (иначе будет вечный цикл)
            print("[RABBIT] invalid json payload; dropping")
            channel.basic_ack(delivery_tag=method_frame.delivery_tag)
            return
        # 2
        input_json = json.loads(body_mq)
        user_id = input_json.get("user_id")
        if not user_id:
            print("[RABBIT] missing user_id; dropping")
            channel.basic_ack(delivery_tag=method_frame.delivery_tag)
            return

        # notice: delete this print after tests:
        print(f"[RABBIT] user_id is: {user_id}")
        # 3
        now = time.time()

        redis_connection.rpush(
            _buffer_key(user_id),
            json.dumps(input_json, ensure_ascii=False)
        )
        # чтобы ключи не жили вечно и не создавали вечный ready-loop
        redis_connection.expire(_buffer_key(user_id), KEY_TTL_SECONDS)
        # notice: delete this print after tests
        print(f"[REDIS] pushed to buffer user_id={user_id}")
        redis_connection.set(_last_message_time_key(user_id), now, ex=KEY_TTL_SECONDS)

        # ACK только после успешной записи в Redis
        channel.basic_ack(delivery_tag=method_frame.delivery_tag)

    except Exception as e:
        print(f"ERROR IN CALLBACK: \n{e}")
        # Транзиентные ошибки (Redis и т.п.) -> requeue
        channel.basic_nack(delivery_tag=method_frame.delivery_tag, requeue=True)


def time_manager():
    pin_workers_cores()
    while True:
        try:
            now = time.time()
            keys = redis_connection.keys("rabbit:last_message_time:*")

            for key in keys:
                user_id = key.split(":")[-1]

                if redis_connection.exists(_ready_key(user_id)):
                    continue

                # Пока идет обработка user_id, не ставим ready (иначе будет спам "already locked").
                # Новые сообщения все равно копятся в buffer, и ready будет выставлен после снятия lock.
                if redis_connection.exists(_processing_key(user_id)):
                    continue
                # Если inflight не пустой, значит воркер уже забрал пачку.
                # Здесь ready не нужен; за восстановление отвечает recovery-блок ниже.
                if redis_connection.llen(_inflight_key(user_id)) > 0:
                    continue

                # Если нечего обрабатывать - чистим метаданные debounce, чтобы не крутиться бесконечно.
                # (Особенно важно при DEBOUNCE_SECONDS=0.)
                if redis_connection.llen(_buffer_key(user_id)) == 0 and redis_connection.llen(_inflight_key(user_id)) == 0:
                    redis_connection.delete(_last_message_time_key(user_id))
                    redis_connection.delete(_ready_key(user_id))
                    continue

                last_time_raw = redis_connection.get(_last_message_time_key(user_id))

                if not last_time_raw:
                    continue

                last_time = float(last_time_raw)

                if now - last_time >= DEBOUNCE_SECONDS:
                    redis_connection.set(
                        _ready_key(user_id),
                        1,
                        nx=True,
                        ex=READY_KEY_TTL_SECONDS
                    )
                    # notice: delete this after tests
                    print(f"[DEBOUNCE] user_id = {user_id} is ready")

            # Recovery: если остались inflight сообщения (например, воркер упал), тоже помечаем ready.
            inflight_keys = redis_connection.keys("rabbit:inflight:*")
            for key in inflight_keys:
                user_id = key.split(":")[-1]
                if redis_connection.exists(_ready_key(user_id)):
                    continue
                # Если кто-то обрабатывает - не трогаем
                if redis_connection.exists(_processing_key(user_id)):
                    continue
                if redis_connection.llen(_inflight_key(user_id)) > 0:
                    redis_connection.set(_ready_key(user_id), 1, nx=True, ex=READY_KEY_TTL_SECONDS)
                    print(f"[RECOVERY] user_id = {user_id} has inflight, marked ready")

        except Exception as e:
            print(f"Error in debounce watching: \n{e}")

        time.sleep(SLEEP_INTERVAL)


def message_dispatcher():
    pin_workers_cores()
    print("dispatcher started")

    workers = []

    while True:
        try:
            workers = [w for w in workers if w.is_alive()]

            if len(workers) >= MAX_WORKERS:
                time.sleep(DISPATCHER_SLEEP)
                continue

            ready_keys = redis_connection.keys("rabbit:ready:*")
            # notice: delete this after tests
            if ready_keys:
                print(f"[DISPATCHER] ready users: {ready_keys}")

            for key in ready_keys:
                if len(workers) >= MAX_WORKERS:
                    break

                user_id = key.split(":")[-1]

                lock_token = uuid.uuid4().hex
                lock_key = _processing_key(user_id)
                locked_user = redis_connection.set(lock_key, lock_token, nx=True, ex=PROCESSING_LOCK_TTL)

                if not locked_user:
                    # notice: delete this after tests
                    print(f"[DISPATCHER] user_id={user_id} already locked")
                    continue

                # notice: delete this after tests
                print(f"[DISPATCHER] locked user_id={user_id}")

                buffer_key = _buffer_key(user_id)
                inflight_key = _inflight_key(user_id)

                # Безопасно переносим сообщения buffer -> inflight (atomic via Lua), чтобы не терять на сбоях.
                moved = 0
                while True:
                    item = _MOVE_ONE_LPOP_RPUSH(keys=[buffer_key, inflight_key], args=[])
                    if item is None:
                        break
                    moved += 1

                inflight_len = redis_connection.llen(inflight_key)
                if inflight_len == 0:
                    # чтобы не крутиться на пустом ready
                    redis_connection.delete(_ready_key(user_id))
                    # и чтобы time_manager не выставлял ready заново, когда реально нет работы
                    if redis_connection.llen(buffer_key) == 0:
                        redis_connection.delete(_last_message_time_key(user_id))
                    _safe_release_lock(lock_key, lock_token)
                    continue
                # inflight тоже ограничиваем по TTL (если воркер умер и recovery не сработал, не копить мусор)
                redis_connection.expire(inflight_key, KEY_TTL_SECONDS)

                # удаляем метаданные debounce для данного user_id (last_message_time НЕ удаляем - нужно для recovery/retry)
                redis_connection.delete(_ready_key(user_id))

                # notice: delete this after tests
                print(f"[DISPATCHER] user_id={user_id} moved={moved} inflight_len={inflight_len}")
                print(f"[DISPATCHER] start worker user_id = {user_id}")

                # параллелим на свободные ядра
                p = multiprocessing.Process(
                    target=worker_entry,
                    args=(user_id, lock_token)
                )
                p.start()
                workers.append(p)

        except Exception as e:
            print(f"Dispatcher Error in: {e}")

        time.sleep(DISPATCHER_SLEEP)


if __name__ == "__main__":
    pin_entry_cores()
    debounce_process = multiprocessing.Process(
        target=time_manager,
        daemon=True
    )
    debounce_process.start()

    dispatcher_process = multiprocessing.Process(
        target=message_dispatcher,
        daemon=False
    )
    dispatcher_process.start()

    start_rabbit_consumer()
