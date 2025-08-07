from rq import Connection, Worker, Queue

from backend.config import get_redis

listen = ["uploads"]


def run_worker() -> None:
    redis_conn = get_redis()
    with Connection(redis_conn):
        worker = Worker(list(map(Queue, listen)))
        worker.work()


if __name__ == "__main__":
    run_worker()
