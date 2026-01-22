import asyncio
import pika
import json, time, os
import multiprocessing
from src.configs.settings import USABLE_RABBIT_QUEUE, USABLE_RABBIT_URL
from src.tools.storage.state_store.redis_usage.redis_connection import redis_connection
from src.utils.gpt_utils import is_json
from src.app import run_worker

rabbit_url = USABLE_RABBIT_URL
rabbit_queue = USABLE_RABBIT_QUEUE
rmq_parameters = pika.URLParameters(rabbit_url)

DEBOUNCE_SECONDS = 10
SLEEP_INTERVAL = 0.3
MAX_WORKERS = 10
DISPATCHER_SLEEP = 0.2
PROCESSING_LOCK_TTL = 80


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


def worker_entry(final_input):
    # notice: delete this after tests
    print(f"[WORKER] started user_id = {final_input.get('user_id')}")

    pin_workers_cores()
    run_worker.run_event(final_input)

    # notice: delete this after tests
    print(f"[WORKER] finished user_id = {final_input.get('user_id')}")

def callback(channel, method_frame, properties, body_mq):
    # pin_entry_cores()

    try:
        # notice: delete this print after tests
        print("[RABBIT] message recieved from rabbit to callback")
        # 1
        if not is_json(body_mq):
            raise ValueError("Rabbit_body is not json")
        # 2
        input_json = json.loads(body_mq)
        user_id = input_json["user_id"]

        # notice: delete this print after tests:
        print(f"[RABBIT] user_id is: {user_id}")
        # 3
        now = time.time()

        redis_connection.rpush(f"rabbit:buffer:{user_id}",
                               json.dumps(input_json, ensure_ascii=False))
        # notice: delete this print after tests
        print(f"[REDIS] pushed to buffer user_id={user_id}")
        redis_connection.set(f"rabbit:last_message_time:{user_id}", now)
        redis_connection.delete(f"rabbit:ready:{user_id}")
        channel.basic_ack(delivery_tag=method_frame.delivery_tag)

    except Exception as e:
        print(f"ERROR IN CALLBACK: \n{e}")
        channel.basic_ack(delivery_tag=method_frame.delivery_tag)


def time_manager():
    pin_entry_cores()
    while True:
        try:
            now = time.time()
            keys = redis_connection.keys("rabbit:last_message_time:*")

            for key in keys:
                user_id = key.decode().split(":")[-1]

                if redis_connection.exists(f"rabbit:ready:{user_id}"):
                    continue

                last_time_raw = redis_connection.get(f"rabbit:last_message_time:{user_id}")

                if not last_time_raw:
                    continue

                last_time = float(last_time_raw)

                if now - last_time >= DEBOUNCE_SECONDS:
                    redis_connection.set(
                        f"rabbit:ready:{user_id}",
                        1,
                        nx=True
                    )

                # notice: delete this after tests
                print(f"[DEBOUNCE] user_id = {user_id} is ready")

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

                user_id = key.decode().split(":")[-1]

                locked_user = redis_connection.set(
                    f"rabbit:processing:{user_id}",
                    1,
                    nx=True,
                    ex=PROCESSING_LOCK_TTL
                )

                if not locked_user:
                    # notice: delete this after tests
                    print(f"[DISPATCHER] user_id={user_id} already locked")
                    continue

                # notice: delete this after tests
                print(f"[DISPATCHER] locked user_id={user_id}")

                raw_buffers = redis_connection.lrange(
                    f"rabbit:buffer:{user_id}", 0, -1
                )

                if not raw_buffers:
                    redis_connection.delete(f"rabbit:processing:{user_id}")
                    continue

                input_dicts = [json.loads(x) for x in raw_buffers]

                first_input = input_dicts[0]

                concat_user_message = chr(10).join(
                    x["question"] for x in input_dicts if x.get("question")
                )

                # в итоге к первому сообщению конкатим все сообщения от юзера, сохраняя остальные параметры
                # первого сообщения, будто к нам прилетело цельное сообщение, вместо нескольких
                final_input = first_input.copy()
                final_input["question"] = concat_user_message

                # notice: delete this after tests
                print(f"[DISPATCHER] user_id = {user_id} messages count = {len(input_dicts)}")
                print(f"[DISPATCHER] user_id = {user_id} concat_message: {concat_user_message}")

                # удаляем все вводные для redis по данному user_id
                redis_connection.delete(f"rabbit:buffer:{user_id}")
                redis_connection.delete(f"rabbit:ready:{user_id}")
                redis_connection.delete(f"rabbit:last_message_time:{user_id}")

                # notice: delete this after tests
                print(f"[DISPATCHER] start worker user_id = {user_id}")

                # параллелим на свободные ядра
                p = multiprocessing.Process(
                    target=worker_entry,
                    args=(final_input,)
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

