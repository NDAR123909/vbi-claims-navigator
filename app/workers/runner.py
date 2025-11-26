"""Worker runner for RQ."""
from rq import Worker, Queue, Connection
from redis import Redis
from app.core.config import settings

if __name__ == "__main__":
    redis_conn = Redis.from_url(settings.REDIS_URL)
    with Connection(redis_conn):
        worker = Worker(['default'])
        worker.work()

