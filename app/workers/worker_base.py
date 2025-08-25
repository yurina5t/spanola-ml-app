import os, json, logging, time
import pika
from sqlmodel import Session
from database.database import get_database_engine
from services.crud.job import get_job, set_status, JobStatus
from services.crud.wallet import top_up_wallet

logger = logging.getLogger(__name__)
RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/")

def start_worker(queue_name: str, handle_job_func):
    params = pika.URLParameters(RABBITMQ_URL)
    connection = pika.BlockingConnection(params)
    channel = connection.channel()
    channel.queue_declare(queue=queue_name, durable=True)
    channel.basic_qos(prefetch_count=1)

    engine = get_database_engine()

    def _callback(ch, method, properties, body):
        try:
            payload = json.loads(body.decode("utf-8"))
            job_id = int(payload["job_id"])
        except Exception as e:
            logger.exception("Bad message: %s", e)
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return

        with Session(engine) as session:
            job = get_job(job_id, session)
            if not job:
                logger.error("Job %s not found", job_id)
                ch.basic_ack(delivery_tag=method.delivery_tag)
                return

            set_status(job, JobStatus.processing, session)
            try:
                result = handle_job_func(job=job, session=session)
                set_status(job, JobStatus.done, session, result=result)
            except Exception as e:
                logger.exception("Job %s failed: %s", job_id, e)
                # вернуть средства пользователю
                try:
                    top_up_wallet(job.user_id, 1.0, session)
                except Exception:
                    logger.error("Refund failed for user_id=%s", job.user_id)
                set_status(job, JobStatus.failed, session, error=str(e))
            finally:
                ch.basic_ack(delivery_tag=method.delivery_tag)

    channel.basic_consume(queue=queue_name, on_message_callback=_callback)
    logger.info("Worker listening on %s", queue_name)
    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        channel.stop_consuming()
        connection.close()
