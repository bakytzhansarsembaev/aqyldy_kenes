import pika
import os

# Настройки из settings
RABBIT_URL = 'amqp://admin:FuzXKWUV3Mos4h4T3E@10.207.48.24:5672/admin'
QUEUE = 'test_messages'

params = pika.URLParameters(RABBIT_URL)
params.heartbeat = 60

connection = pika.BlockingConnection(params)
channel = connection.channel()
channel.queue_declare(queue=QUEUE, durable=True)
channel.basic_qos(prefetch_count=1)

print(f"PID: {os.getpid()}")
print(f"Listening queue: {QUEUE}")
print("Waiting for messages...\n")

def callback(ch, method, properties, body):
    print(f"[MSG] {body.decode()}")
    ch.basic_ack(delivery_tag=method.delivery_tag)

channel.basic_consume(queue=QUEUE, on_message_callback=callback, auto_ack=False)
channel.start_consuming()
