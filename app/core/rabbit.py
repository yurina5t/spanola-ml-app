import json, os, pika
from contextlib import contextmanager

RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/")

EXCHANGE = "ml_tasks"
EXCHANGE_TYPE = "direct"  # по ключам маршрутизации: comic / grammar / vocab
ROUTING_KEYS = {"comic": "comic", "grammar": "grammar", "vocab": "vocab"}

def _params():
    return pika.URLParameters(RABBITMQ_URL)

def declare_topology(ch: pika.adapters.blocking_connection.BlockingChannel):
    ch.exchange_declare(exchange=EXCHANGE, exchange_type=EXCHANGE_TYPE, durable=True)
    # очереди по моделям
    for q in ROUTING_KEYS.values():
        ch.queue_declare(queue=q, durable=True)
        ch.queue_bind(exchange=EXCHANGE, queue=q, routing_key=q)

@contextmanager
def producer_channel():
    conn = pika.BlockingConnection(_params())
    try:
        ch = conn.channel()
        declare_topology(ch)
        yield ch
    finally:
        conn.close()

def publish_task(routing_key: str, payload: dict):
    with producer_channel() as ch:
        ch.basic_publish(
            exchange=EXCHANGE,
            routing_key=routing_key,
            body=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            properties=pika.BasicProperties(
                delivery_mode=2,  # persistent
                content_type="application/json",
            ),
        )
