import os
from redis import Redis
from rq import Connection, Worker, Queue

listen = ["uploads"]

redis_host = os.environ.get("REDIS_HOST", "redis")
redis_port = int(os.environ.get("REDIS_PORT", 6379))


def run_worker() -> None:
    redis_conn = Redis(host=redis_host, port=redis_port)
    with Connection(redis_conn):
        worker = Worker(list(map(Queue, listen)))
        worker.work()


if __name__ == "__main__":
    run_worker()
